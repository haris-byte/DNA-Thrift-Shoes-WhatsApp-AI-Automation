from app.inventory.database import InventoryRepository
from app.inventory.pricing import calculate_price
from app.models.inventory_models import (
    InventoryMatchResult,
    MatchType,
    StockStatus,
)
from app.models.shoe_models import ShoeQuery


class InventoryService:
    def __init__(self, repository: InventoryRepository) -> None:
        self.repository = repository

    def lookup(self, query: ShoeQuery) -> InventoryMatchResult:
        if query.brand is None or query.model is None or query.size_us is None:
            raise ValueError("Inventory lookup requires brand, model, and US size.")

        exact_matches = self.repository.exact_matches(query.brand, query.model, query.size_us)
        if exact_matches:
            item = exact_matches[0]
            price = calculate_price(item)
            availability = item.stock_status.value.replace("_", " ")
            message = (
                f"{item.product_name} is available in US {item.size_us:g}. "
                f"Condition: {item.condition_score}/10. "
                f"Price: Rs. {price.final_price:,}. "
                f"Status: {availability}. "
                f"Details: {item.description}"
            )
            if item.stock_status != StockStatus.IN_STOCK:
                message += " This exact pair cannot be reserved right now."
            return InventoryMatchResult(
                match_type=MatchType.EXACT,
                query=query,
                exact_match=item,
                price=price,
                message=message,
            )

        partial = self.repository.same_model(query.brand, query.model, query.size_us)
        if partial:
            sizes = ", ".join(f"US {item.size_us:g}" for item in partial)
            return InventoryMatchResult(
                match_type=MatchType.PARTIAL,
                query=query,
                alternatives=partial,
                message=(
                    f"We do not have {query.model} in US {query.size_us:g} right now, "
                    f"but the same model is available in {sizes}."
                ),
            )

        alternatives = self.repository.brand_alternatives(query.brand)
        if alternatives:
            options = "; ".join(
                f"{item.product_name} (US {item.size_us:g}, {item.condition_score}/10)"
                for item in alternatives[:3]
            )
            return InventoryMatchResult(
                match_type=MatchType.NO_MATCH,
                query=query,
                alternatives=alternatives[:3],
                message=(
                    f"We do not currently have {query.model} in US {query.size_us:g}. "
                    f"Available {query.brand} alternatives: {options}."
                ),
            )

        return InventoryMatchResult(
            match_type=MatchType.NO_MATCH,
            query=query,
            message=(
                "We do not currently have that model or a close brand alternative in stock. "
                "Send another model, size, or shoe photo."
            ),
        )
