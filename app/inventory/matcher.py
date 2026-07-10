from app.models.shoe_models import (
    InventoryItem,
    InventoryMatchResult,
    MatchType,
    ShoeQuery,
    StockStatus,
)
from app.inventory.pricing import calculate_price
from app.inventory.sample_inventory import SAMPLE_INVENTORY


def normalize(value: str) -> str:
    return value.lower().strip()


def brand_matches(item: InventoryItem, query: ShoeQuery) -> bool:
    if query.brand is None:
        return True

    return normalize(item.brand) == normalize(query.brand)


def model_matches(item: InventoryItem, query: ShoeQuery) -> bool:
    if query.model is None:
        return False

    return normalize(item.model) == normalize(query.model)


def size_matches(item: InventoryItem, query: ShoeQuery) -> bool:
    if query.size_us is None:
        return False

    return item.size_us == query.size_us


def sort_inventory_priority(items: list[InventoryItem]) -> list[InventoryItem]:
    return sorted(
        items,
        key=lambda item: (
            item.stock_status != StockStatus.IN_STOCK,
            -item.condition_score,
            item.size_us
        )
    )


def find_exact_matches(query: ShoeQuery) -> list[InventoryItem]:
    matches = [
        item
        for item in SAMPLE_INVENTORY
        if brand_matches(item, query)
        and model_matches(item, query)
        and size_matches(item, query)
    ]

    return sort_inventory_priority(matches)


def find_partial_matches(query: ShoeQuery) -> list[InventoryItem]:
    if query.model is None:
        return []

    matches = [
        item
        for item in SAMPLE_INVENTORY
        if brand_matches(item, query)
        and model_matches(item, query)
        and item.stock_status == StockStatus.IN_STOCK
    ]

    if query.size_us is not None:
        matches = sorted(
            matches,
            key=lambda item: (
                abs(item.size_us - query.size_us),
                -item.condition_score
            )
        )

    return matches[:3]


def find_brand_alternatives(query: ShoeQuery) -> list[InventoryItem]:
    if query.brand is None:
        return []

    matches = [
        item
        for item in SAMPLE_INVENTORY
        if brand_matches(item, query)
        and item.stock_status == StockStatus.IN_STOCK
    ]

    return sort_inventory_priority(matches)[:3]


def lookup_inventory(query: ShoeQuery) -> InventoryMatchResult:
    exact_matches = find_exact_matches(query)

    if exact_matches:
        best_match = exact_matches[0]
        price = calculate_price(best_match)

        message = (
            f"Yes, we have {best_match.product_name} in US {best_match.size_us}. "
            f"Condition: {best_match.condition_score}/10. "
            f"Price: Rs. {price.final_price}. "
            f"Availability: {best_match.stock_status.value}."
        )

        return InventoryMatchResult(
            match_type=MatchType.EXACT,
            query=query,
            exact_match=best_match,
            alternatives=[],
            price=price,
            message=message
        )

    partial_matches = find_partial_matches(query)

    if partial_matches:
        sizes = ", ".join([f"US {item.size_us}" for item in partial_matches])

        message = (
            f"We do not have the exact {query.model} in US {query.size_us} right now, "
            f"but we have nearby/available options in {sizes}."
        )

        return InventoryMatchResult(
            match_type=MatchType.PARTIAL,
            query=query,
            exact_match=None,
            alternatives=partial_matches,
            price=None,
            message=message
        )

    brand_alternatives = find_brand_alternatives(query)

    if brand_alternatives:
        models = ", ".join(
            [f"{item.product_name} US {item.size_us}" for item in brand_alternatives]
        )

        message = (
            f"We do not currently have {query.model} in US {query.size_us}, "
            f"but we do have these {query.brand} options: {models}."
        )

        return InventoryMatchResult(
            match_type=MatchType.NO_MATCH,
            query=query,
            exact_match=None,
            alternatives=brand_alternatives,
            price=None,
            message=message
        )

    message = (
        "We do not currently have that model in stock. "
        "You can send another shoe name/photo or ask for available Nike, Adidas, Vans, or Converse shoes."
    )

    return InventoryMatchResult(
        match_type=MatchType.NO_MATCH,
        query=query,
        exact_match=None,
        alternatives=[],
        price=None,
        message=message
    )