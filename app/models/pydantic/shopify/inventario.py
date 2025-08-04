from app.models.pydantic.base import Base


class Address(Base):
    city: str | None = None
    country: str | None = None
    address1: str | None = None


class Location(Base):
    legacyResourceId: str | None = None
    address: Address = Address()


class Quantitie(Base):
    name: str | None = None
    quantity: int | None = None


class InventoryLevel(Base):
    quantities: list[Quantitie] = list[Quantitie]([Quantitie()])
    location: Location = Location()


class InventoryLevelNodes(Base):
    nodes: list[InventoryLevel] = []


class InventoryItem(Base):
    legacyResourceId: int | None = None
    inventoryLevels: InventoryLevelNodes = InventoryLevelNodes()


class InventoryItemNodes(Base):
    nodes: list[InventoryItem] = []


class InventoryItems(Base):
    inventoryItems: InventoryItemNodes = InventoryItemNodes()


class InventoryLevelsResponse(Base):
    data: InventoryItems = InventoryItems()


class Variant(Base):
    legacyResourceId: int | None = None
    inventoryQuantity: int | None = None
    title: str | None = None
    price: float | None = None
    inventoryItem: InventoryItem = InventoryItem()


class VariantNodes(Base):
    nodes: list[Variant] = []


class Variants(Base):
    productVariants: VariantNodes = VariantNodes()


class VariantsResponse(Base):
    data: Variants = Variants()


class PageInfo(Base):
    hasNextPage: bool | None = None
    endCursor: str | None = None


class Product(Base):
    legacyResourceId: int | None = None
    title: str | None = None
    variants: list[Variant] = []
    inventory_levels: list[InventoryLevel] = []


class ProductNodes(Base):
    nodes: list[Product] = []


class Products(Base):
    products: ProductNodes = ProductNodes()


class ProductsResponse(Base):
    data: Products = Products()
