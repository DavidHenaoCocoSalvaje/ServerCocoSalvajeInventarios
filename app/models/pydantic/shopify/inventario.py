# app.models.pydantic.shopify.inventario

from pydantic import Field
from app.models.pydantic.base import Base


class Address(Base):
    city: str | None = ''
    province: str | None = ''
    country: str | None = ''
    address1: str | None = ''


class Location(Base):
    legacyResourceId: int | None = 0
    address: Address | None = Address()


class Quantitie(Base):
    quantity: int | None = None


class InventoryLevel(Base):
    class Item(Base):
        class Variant(Base):
            legacyResourceId: int | None = 0

        variant: Variant | None = Variant()

    item: Item | None = Item()
    quantities: list[Quantitie] | None = Field(default_factory=list)
    location: Location | None = Location()


class InventoryLevelNodes(Base):
    nodes: list[InventoryLevel] | None = Field(default_factory=list)


class InventoryItem(Base):
    legacyResourceId: int | None = 0
    sku: str | None = ''
    inventoryLevels: InventoryLevelNodes | None = InventoryLevelNodes()


class InventoryItemNodes(Base):
    nodes: list[InventoryItem] | None = Field(default_factory=list)


class InventoryItems(Base):
    inventoryItems: InventoryItemNodes | None = InventoryItemNodes()


class InventoryLevelsResponse(Base):
    data: InventoryItems | None = InventoryItems()


class Variant(Base):
    class Product(Base):
        legacyResourceId: int | None = 0

    product: Product | None = Product()
    legacyResourceId: int | None = 0
    inventoryQuantity: int | None = None
    title: str | None = ''
    price: float | None = None
    inventoryItem: InventoryItem | None = InventoryItem()
    sku: str | None = ''
    inventoryLevels: list[InventoryLevel] | None = Field(default_factory=list)


class VariantNodes(Base):
    nodes: list[Variant] | None = Field(default_factory=list)


class Variants(Base):
    productVariants: VariantNodes | None = VariantNodes()


class VariantsResponse(Base):
    data: Variants | None = Variants()


class PageInfo(Base):
    hasNextPage: bool | None = None
    endCursor: str | None = ''


class Product(Base):
    legacyResourceId: int | None = 0
    title: str | None = ''
    variants: list[Variant] | None = Field(default_factory=list)


class ProductNodes(Base):
    nodes: list[Product] | None = Field(default_factory=list)


class Products(Base):
    products: ProductNodes | None = ProductNodes()


class ProductsResponse(Base):
    data: Products | None = Products()
