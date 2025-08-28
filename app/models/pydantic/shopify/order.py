# app.models.pydantic.shopify.payloads

# Modelos de payloads enviados por Shopify en webhooks

from datetime import datetime
from enum import Enum
from pydantic import Field, computed_field
from app.internal.gen.utilities import divide
from app.models.pydantic.base import Base


class FinancialStatus(Enum):
    """_summary_
    AUTHORIZED
    Displayed as Authorized. The payment provider has validated the customer's payment information. This status appears only for manual payment capture and indicates payments should be captured before the authorization period expires.

    Anchor to EXPIRED
    Displayed as Expired. Payment wasn't captured before the payment provider's deadline on an authorized order. Some payment providers use this status to indicate failed payment processing.

    Anchor to PAID
    Displayed as Paid. Payment was automatically or manually captured, or the order was marked as paid.

    Anchor to PARTIALLY_PAID
    Displayed as Partially paid. A payment was manually captured for the order with an amount less than the full order value.

    Anchor to PARTIALLY_REFUNDED
    Displayed as Partially refunded. The amount refunded to a customer is less than the full amount paid for an order.

    Anchor to PENDING
    Displayed as Pending. Orders have this status when the payment provider needs time to complete the payment, or when manual payment methods are being used.

    Anchor to REFUNDED
    Displayed as Refunded. The full amount paid for an order was refunded to the customer.

    Anchor to VOIDED
    Displayed as Voided. An unpaid (payment authorized but not captured) order was manually canceled.
    """

    PAID = 'paid'
    PARTIALLY_PAID = 'partially_paid'
    PARTIALLY_REFUNDED = 'partially_refunded'
    PENDING = 'pending'
    AUTHORIZED = 'authorized'
    EXPIRED = 'expired'
    REFUNDED = 'refunded'
    VOIDED = 'voided'


class OrderWebHook(Base):
    admin_graphql_api_id: str = ''  # Webhook con guiones bajos


class Address(Base):
    firstName: str = ''
    lastName: str = ''
    company: str = ''
    address1: str = ''
    address2: str = ''
    province: str = ''
    country: str = ''
    city: str = ''
    phone: str = ''
    zip: str = ''  # Se deja como str porque es un campo ingresado por el cliente y no se restringe su tipo.
    formatted: list[str] = []


class Customer(Base):
    firstName: str = ''
    lastName: str = ''
    id: str = ''


class ShopMoney(Base):
    amount: float = 0
    currencyCode: str = ''


class OriginalPriceSet(Base):
    shopMoney: ShopMoney = ShopMoney()


class DiscountedUnitPriceSet(Base):
    """_summary_
    Representa el precio de venta luego de aplicar descuentos.
    """

    shopMoney: ShopMoney = ShopMoney()


class LineItem(Base):
    class Variant(Base):
        compareAtPrice: float = 0

    name: str = ''
    quantity: int = 0
    variant: Variant = Variant()
    originalUnitPriceSet: OriginalPriceSet = OriginalPriceSet()
    discountedUnitPriceSet: DiscountedUnitPriceSet = DiscountedUnitPriceSet()
    sku: str = ''

    @computed_field
    @property
    def unit_price(self) -> int:
        amount = self.originalUnitPriceSet.shopMoney.amount
        amount = amount if amount > 0 else self.variant.compareAtPrice
        return round(amount) if amount > 0 else 0

    @computed_field
    @property
    def discounted_unit_price(self) -> int:
        amount = self.discountedUnitPriceSet.shopMoney.amount
        amount = amount if amount > 0 else self.unit_price
        return round(amount) if amount > 0 else 0

    @computed_field
    @property
    def porc_discount(self) -> int:
        """_summary_
        Retorna el porcentaje de descuento expresado como un flotante entre 0 y 100.
        """
        if self.unit_price == 0:
            return 100
        else:
            discount_amount = self.unit_price - self.discounted_unit_price
            return round(divide(discount_amount, self.discounted_unit_price) * 100)

    def discounted_unit_price_iva_discount(self, IVA: float) -> int:
        return round(self.discounted_unit_price / (1 + IVA))


class PageInfo(Base):
    endCursor: str = ''
    hasNextPage: bool = False


class LineItemsNodes(Base):
    nodes: list[LineItem] = []
    pageInfo: PageInfo = PageInfo()


class ShippingLine(Base):
    originalPriceSet: OriginalPriceSet = OriginalPriceSet()


class Transaction(Base):
    gateway: str = ''
    paymentId: str = ''


class App(Base):
    name: str = ''


class Order(Base):
    fullyPaid: bool = False
    email: str = ''
    number: int = 0
    createdAt: datetime = Field(default_factory=datetime.now)
    app: App = App()
    customer: Customer = Customer()
    transactions: list[Transaction] = []
    billingAddress: Address = Address()
    shippingAddress: Address = Address()
    shippingLine: ShippingLine = ShippingLine()
    lineItems: LineItemsNodes = LineItemsNodes()


class OrderData(Base):
    order: Order = Order()  # Cuando no se encuentra la orden la respuesta llega con order: null


class OrderResponse(Base):
    data: OrderData = OrderData()

    def valid(self) -> bool:
        return self.data.order.number != 0
