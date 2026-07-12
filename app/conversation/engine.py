import re
from app.core.config import Settings
from app.inventory.database import IdempotencyRepository, SessionRepository
from app.inventory.service import InventoryService
from app.models.conversation_models import BotResponse, ConversationSession, ConversationState
from app.models.inventory_models import MatchType, StockStatus
from app.models.shoe_models import ShoeQuery
from app.models.webhook_models import IncomingMessage, MessageType
from app.nlp.text_parser import HybridTextParser, build_clarification, missing_fields_for
from app.vision.photo_pipeline import PhotoPipeline


class ConversationEngine:
    def __init__(
        self,
        settings: Settings,
        sessions: SessionRepository,
        idempotency: IdempotencyRepository,
        text_parser: HybridTextParser,
        photo_pipeline: PhotoPipeline,
        inventory: InventoryService,
    ) -> None:
        self.settings = settings
        self.sessions = sessions
        self.idempotency = idempotency
        self.text_parser = text_parser
        self.photo_pipeline = photo_pipeline
        self.inventory = inventory

    @staticmethod
    def _transition(session: ConversationSession, **updates: object) -> ConversationSession:
        data = session.model_dump()
        data.update(updates)
        return ConversationSession.model_validate(data)

    @staticmethod
    def merge_queries(previous: ShoeQuery | None, current: ShoeQuery) -> ShoeQuery:
        if previous is None:
            return current
        return ShoeQuery(
            brand=current.brand or previous.brand,
            model=current.model or previous.model,
            size_us=current.size_us if current.size_us is not None else previous.size_us,
            condition_score=(
                current.condition_score
                if current.condition_score is not None
                else previous.condition_score
            ),
            condition_notes=current.condition_notes or previous.condition_notes,
            confidence=max(previous.confidence, current.confidence),
            source=f"{previous.source}+{current.source}",
        )

    @staticmethod
    def fallback_reply() -> str:
        return (
            "I still cannot identify the exact pair after two clarification attempts. "
            "Please send a clear shoe photo with the logo and size tag, browse another model, "
            "or ask for a DNA Thrift team member."
        )

    def _response(self, message: IncomingMessage, session: ConversationSession, reply: str) -> BotResponse:
        self.sessions.save(session)
        response = BotResponse(
            sender_id=message.sender_id,
            message_id=message.message_id,
            state=session.state,
            reply=reply,
            session=session,
        )
        self.idempotency.save(response)
        return response

    def _ask(
        self,
        message: IncomingMessage,
        session: ConversationSession,
        question: str,
        target_state: ConversationState,
        pending_query: ShoeQuery | None,
    ) -> BotResponse:
        same_question = session.last_clarification_question == question
        failed_attempts = (
            session.failed_clarification_attempts + 1 if same_question else 0
        )

        if failed_attempts >= self.settings.max_clarification_attempts:
            updated = self._transition(
                session,
                state=ConversationState.FALLBACK_HUMAN,
                pending_query=pending_query,
                failed_clarification_attempts=failed_attempts,
                last_clarification_question=question,
            )
            return self._response(message, updated, self.fallback_reply())

        updated = self._transition(
            session,
            state=target_state,
            pending_query=pending_query,
            failed_clarification_attempts=failed_attempts,
            last_clarification_question=question,
        )
        return self._response(message, updated, question)

    def _present(self, message: IncomingMessage, session: ConversationSession, query: ShoeQuery) -> BotResponse:
        result = self.inventory.lookup(query)
        if (
            result.match_type == MatchType.EXACT
            and result.exact_match is not None
            and result.exact_match.stock_status == StockStatus.IN_STOCK
        ):
            state = ConversationState.AWAITING_PURCHASE_INTENT
            reply = result.message + " Would you like to reserve this pair, see alternatives, or cancel?"
        else:
            state = ConversationState.PRESENTING_RESULT
            reply = result.message

        updated = self._transition(
            session,
            state=state,
            pending_query=query,
            last_inventory_result=result,
            failed_clarification_attempts=0,
            last_clarification_question=None,
        )
        return self._response(message, updated, reply)

    def _handle_text_query(
        self,
        message: IncomingMessage,
        session: ConversationSession,
    ) -> BotResponse:
        parsed = self.text_parser.parse(message.text or "")
        combined = self.merge_queries(session.pending_query, parsed.query)
        missing = missing_fields_for(combined)
        if missing:
            target = (
                ConversationState.AWAITING_SIZE_CONFIRMATION
                if missing == ["size_us"]
                else ConversationState.IDENTIFYING_SHOE
            )
            return self._ask(
                message,
                session,
                build_clarification(missing),
                target,
                combined,
            )
        return self._present(message, session, combined)

    def _handle_image_query(
        self,
        message: IncomingMessage,
        session: ConversationSession,
    ) -> BotResponse:
        photo = self.photo_pipeline.analyze(message.image_source or "")
        combined = self.merge_queries(session.pending_query, photo.query)
        if message.text:
            caption_query = self.text_parser.parse(message.text).query
            combined = self.merge_queries(combined, caption_query)
        missing = missing_fields_for(combined)
        if missing:
            target = (
                ConversationState.AWAITING_SIZE_CONFIRMATION
                if missing == ["size_us"]
                else ConversationState.IDENTIFYING_SHOE
            )
            question = photo.clarification_question or build_clarification(missing)
            return self._ask(message, session, question, target, combined)
        return self._present(message, session, combined)

    def _handle_purchase_intent(
        self,
        message: IncomingMessage,
        session: ConversationSession,
    ) -> BotResponse:
        if message.message_type != MessageType.TEXT:
            return self._ask(
                message,
                session,
                "Please reply: reserve, alternatives, or cancel.",
                ConversationState.AWAITING_PURCHASE_INTENT,
                session.pending_query,
            )

        text = re.sub(r"\s+", " ", (message.text or "").lower().strip())
        if re.search(r"\b(reserve|book|hold|confirm|yes)\b", text):
            updated = self._transition(session, state=ConversationState.PRESENTING_RESULT)
            return self._response(
                message,
                updated,
                (
                    "Your reservation interest has been recorded. A DNA Thrift team member must "
                    "confirm stock locking and payment before the reservation is final."
                ),
            )
        if re.search(r"\b(alternative|alternatives|other|more|show more)\b", text):
            fresh = ConversationSession(sender_id=session.sender_id)
            return self._response(
                message,
                fresh,
                "Send another shoe model and US size, or upload another clear shoe photo.",
            )
        if re.search(r"\b(cancel|no|nope|not now)\b", text):
            fresh = ConversationSession(sender_id=session.sender_id)
            return self._response(
                message,
                fresh,
                "No problem. Send another model, size, or shoe photo whenever you are ready.",
            )

        parsed = self.text_parser.parse(message.text or "")
        if parsed.query.model or parsed.query.size_us or parsed.query.brand:
            fresh = ConversationSession(sender_id=session.sender_id)
            return self._handle_text_query(message, fresh)

        return self._ask(
            message,
            session,
            "Would you like to reserve this pair, see alternatives, or cancel?",
            ConversationState.AWAITING_PURCHASE_INTENT,
            session.pending_query,
        )

    def handle(self, message: IncomingMessage) -> BotResponse:
        cached = self.idempotency.get(message.message_id)
        if cached is not None:
            return BotResponse.model_validate(
                {**cached.model_dump(), "duplicate_delivery": True}
            )

        session = self.sessions.get(message.sender_id)

        if session.state == ConversationState.AWAITING_PURCHASE_INTENT:
            return self._handle_purchase_intent(message, session)

        if session.state in {
            ConversationState.FALLBACK_HUMAN,
            ConversationState.PRESENTING_RESULT,
        }:
            session = ConversationSession(sender_id=message.sender_id)

        if message.message_type == MessageType.TEXT:
            return self._handle_text_query(message, session)
        return self._handle_image_query(message, session)
