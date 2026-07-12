from app.inventory.database import InventoryRepository, SQLiteDatabase
from app.inventory.pricing import calculate_price
from app.inventory.service import InventoryService
from app.models.inventory_models import MatchType
from app.models.shoe_models import ShoeQuery


def build_service(settings) -> InventoryService:
    database = SQLiteDatabase(settings.database_path)
    database.initialize()
    return InventoryService(InventoryRepository(database))


def test_exact_air_force_price_is_condition_adjusted(settings) -> None:
    result = build_service(settings).lookup(
        ShoeQuery(brand="Nike", model="Air Force 1", size_us=10, confidence=1, source="test")
    )
    assert result.match_type == MatchType.EXACT
    assert result.exact_match is not None
    assert result.exact_match.product_name == "Nike Air Force 1 White"
    assert result.price is not None
    assert result.price.final_price == 9450


def test_partial_match_returns_nearby_sizes(settings) -> None:
    result = build_service(settings).lookup(
        ShoeQuery(brand="Nike", model="Air Jordan 1", size_us=8, confidence=1, source="test")
    )
    assert result.match_type == MatchType.PARTIAL
    assert {item.size_us for item in result.alternatives} >= {9.0, 10.0}


def test_no_model_match_returns_brand_alternatives(settings) -> None:
    result = build_service(settings).lookup(
        ShoeQuery(brand="Nike", model="Unknown Runner", size_us=10, confidence=1, source="test")
    )
    assert result.match_type == MatchType.NO_MATCH
    assert result.alternatives


def test_pricing_tiers() -> None:
    from app.models.inventory_models import InventoryItem, StockStatus

    item = InventoryItem(
        product_id="T",
        product_name="Test",
        brand="Test",
        model="Test",
        size_us=10,
        condition_score=6,
        base_price=10000,
        stock_status=StockStatus.IN_STOCK,
        description="Test item",
    )
    assert calculate_price(item).final_price == 7000
