from app.models.inventory_models import InventoryItem, PriceBreakdown


def condition_multiplier(condition_score: int) -> float:
    if condition_score >= 9:
        return 1.0
    if condition_score >= 7:
        return 0.85
    if condition_score >= 5:
        return 0.70
    return 0.55


def calculate_price(item: InventoryItem) -> PriceBreakdown:
    multiplier = condition_multiplier(item.condition_score)
    final_price = round(item.base_price * multiplier)
    return PriceBreakdown(
        base_price=item.base_price,
        condition_score=item.condition_score,
        condition_multiplier=multiplier,
        final_price=final_price,
        currency="PKR",
    )
