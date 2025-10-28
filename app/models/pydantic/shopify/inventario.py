# app.models.pydantic.shopify.inventario

from app.models.pydantic.base import Base


class AddressLocation(Base):
    city: str = ''
    province: str = ''
    country: str = ''
    address1: str = ''
    formatted: list[str] = []


class Location(Base):
    legacyResourceId: int = 0
    address: AddressLocation = AddressLocation()


class Quantitie(Base):
    quantity: int = 0


class InventoryLevel(Base):
    class Item(Base):
        class InventoryLevelVariant(Base):
            legacyResourceId: int = 0

        variant: InventoryLevelVariant = InventoryLevelVariant()

    item: Item = Item()
    quantities: list[Quantitie] = []
    location: Location = Location()


class InventoryLevelNodes(Base):
    nodes: list[InventoryLevel] = []


class InventoryItem(Base):
    legacyResourceId: int = 0
    sku: str = ''
    inventoryLevels: InventoryLevelNodes = InventoryLevelNodes()


class InventoryItemNodes(Base):
    nodes: list[InventoryItem] = []


class InventoryItems(Base):
    inventoryItems: InventoryItemNodes = InventoryItemNodes()


class InventoryLevelsResponse(Base):
    data: InventoryItems = InventoryItems()


class Variant(Base):
    class VariantProduct(Base):
        legacyResourceId: int = 0

    product: VariantProduct = VariantProduct()
    legacyResourceId: int = 0
    inventoryQuantity: int = 0
    title: str = ''
    price: float = 0.0
    inventoryItem: InventoryItem = InventoryItem()
    sku: str = ''


class VariantNodes(Base):
    nodes: list[Variant] = []


class Variants(Base):
    productVariants: VariantNodes = VariantNodes()


class VariantsResponse(Base):
    data: Variants = Variants()


class PageInfo(Base):
    hasNextPage: bool = False
    endCursor: str = ''


class Product(Base):
    legacyResourceId: int = 0
    title: str = ''
    variants: list[Variant] = []


class ProductNodes(Base):
    nodes: list[Product] = []


class Products(Base):
    products: ProductNodes = ProductNodes()


class ProductsResponse(Base):
    data: Products = Products()
