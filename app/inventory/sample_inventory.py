from app.models.shoe_models import InventoryItem, StockStatus


SAMPLE_INVENTORY: list[InventoryItem] = [
    InventoryItem(
        product_id="DNA-001",
        product_name="Nike Air Jordan 1 Retro High",
        brand="Nike",
        model="Air Jordan 1",
        size_us=10.0,
        condition_score=9,
        base_price=18500,
        stock_status=StockStatus.IN_STOCK,
        description="Lightly used premium thrift pair with minimal creasing."
    ),
    InventoryItem(
        product_id="DNA-002",
        product_name="Nike Air Jordan 1 Mid",
        brand="Nike",
        model="Air Jordan 1",
        size_us=9.0,
        condition_score=8,
        base_price=16000,
        stock_status=StockStatus.IN_STOCK,
        description="Used pair with light toe-box creasing and clean outsole."
    ),
    InventoryItem(
        product_id="DNA-003",
        product_name="Nike Air Jordan 1 Low",
        brand="Nike",
        model="Air Jordan 1",
        size_us=11.0,
        condition_score=7,
        base_price=15000,
        stock_status=StockStatus.IN_STOCK,
        description="Good thrift condition with visible wear near heel collar."
    ),
    InventoryItem(
        product_id="DNA-004",
        product_name="Nike Air Force 1 White",
        brand="Nike",
        model="Air Force 1",
        size_us=10.0,
        condition_score=6,
        base_price=13500,
        stock_status=StockStatus.IN_STOCK,
        description="Visible creasing and moderate sole wear, still wearable."
    ),
    InventoryItem(
        product_id="DNA-005",
        product_name="Nike Air Force 1 Black",
        brand="Nike",
        model="Air Force 1",
        size_us=8.0,
        condition_score=8,
        base_price=14500,
        stock_status=StockStatus.RESERVED,
        description="Reserved pair in good condition with minor outsole wear."
    ),
    InventoryItem(
        product_id="DNA-006",
        product_name="Adidas Ultraboost 21",
        brand="Adidas",
        model="Ultraboost",
        size_us=10.0,
        condition_score=8,
        base_price=17000,
        stock_status=StockStatus.IN_STOCK,
        description="Comfort running shoe with clean upper and light sole marks."
    ),
    InventoryItem(
        product_id="DNA-007",
        product_name="Adidas Yeezy Boost 350",
        brand="Adidas",
        model="Yeezy",
        size_us=9.0,
        condition_score=7,
        base_price=24000,
        stock_status=StockStatus.IN_STOCK,
        description="Premium thrift pair with visible outsole wear."
    ),
    InventoryItem(
        product_id="DNA-008",
        product_name="Vans Old Skool Classic",
        brand="Vans",
        model="Old Skool",
        size_us=10.0,
        condition_score=8,
        base_price=9000,
        stock_status=StockStatus.IN_STOCK,
        description="Clean casual pair with minor canvas fading."
    ),
    InventoryItem(
        product_id="DNA-009",
        product_name="Converse Chuck Taylor High",
        brand="Converse",
        model="Chuck Taylor",
        size_us=9.0,
        condition_score=6,
        base_price=8000,
        stock_status=StockStatus.SOLD_OUT,
        description="Classic high-top pair, currently sold out."
    ),
]