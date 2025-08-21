# app.models.pydantic.shopify.inventario

from pydantic import Field
from app.models.pydantic.base import Base


class Address(Base):
    city: str = ''
    province: str = ''
    country: str = ''
    address1: str = ''


class Location(Base):
    legacyResourceId: int = 0
    address: Address = Address()


class Quantitie(Base):
    quantity: int | None = None


class InventoryLevel(Base):
    class Item(Base):
        class Variant(Base):
            legacyResourceId: int = 0

        variant: Variant = Variant()

    item: Item = Item()
    quantities: list[Quantitie] = Field(default_factory=list)
    location: Location = Location()


class InventoryLevelNodes(Base):
    nodes: list[InventoryLevel] = Field(default_factory=list)


class InventoryItem(Base):
    legacyResourceId: int = 0
    sku: str = ''
    inventoryLevels: InventoryLevelNodes = InventoryLevelNodes()


class InventoryItemNodes(Base):
    nodes: list[InventoryItem] = Field(default_factory=list)


class InventoryItems(Base):
    inventoryItems: InventoryItemNodes = InventoryItemNodes()


class InventoryLevelsResponse(Base):
    data: InventoryItems = InventoryItems()


class Variant(Base):
    class Product(Base):
        legacyResourceId: int = 0

    product: Product = Product()
    legacyResourceId: int = 0
    inventoryQuantity: int | None = None
    title: str = ''
    price: float | None = None
    inventoryItem: InventoryItem = InventoryItem()
    sku: str = ''
    inventoryLevels: list[InventoryLevel] = Field(default_factory=list)


class VariantNodes(Base):
    nodes: list[Variant] = Field(default_factory=list)


class Variants(Base):
    productVariants: VariantNodes = VariantNodes()


class VariantsResponse(Base):
    data: Variants = Variants()


class PageInfo(Base):
    hasNextPage: bool | None = None
    endCursor: str = ''


class Product(Base):
    legacyResourceId: int = 0
    title: str = ''
    variants: list[Variant] = Field(default_factory=list)


class ProductNodes(Base):
    nodes: list[Product] = Field(default_factory=list)


class Products(Base):
    products: ProductNodes = ProductNodes()


class ProductsResponse(Base):
    data: Products = Products()
