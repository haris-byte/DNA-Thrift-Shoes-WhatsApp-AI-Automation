from app.nlp.text_parser import HybridTextParser, RuleTextParser, extract_size


def test_air_force_query_parses_correctly() -> None:
    result = RuleTextParser().parse("Do you have Air Force 1 size 10?")
    assert result.query.brand == "Nike"
    assert result.query.model == "Air Force 1"
    assert result.query.size_us == 10
    assert result.clarification_needed is False


def test_ambiguous_query_requests_model_and_size() -> None:
    result = RuleTextParser().parse("Nike shoes?")
    assert result.query.brand == "Nike"
    assert result.query.model is None
    assert result.query.size_us is None
    assert result.clarification_needed is True
    assert "model" in (result.clarification_question or "").lower()


def test_bare_size_is_accepted_for_followup() -> None:
    assert extract_size("10") == 10
    assert extract_size("US 10.5") == 10.5


def test_impossible_size_is_rejected() -> None:
    assert extract_size("size 99") is None


def test_hybrid_parser_falls_back_to_rules_without_api(settings) -> None:
    parser = HybridTextParser(settings)
    result = parser.parse("Jordan 1 US 10")
    assert result.query.model == "Air Jordan 1"
    assert result.used_llm is False
