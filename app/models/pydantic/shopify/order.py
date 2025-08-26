# app.models.pydantic.shopify.payloads

# Modelos de payloads enviados por Shopify en webhooks

from datetime import datetime
from enum import Enum
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
    admin_graphql_api_id: str | None = ''  # Webhook con guiones bajos


class BillingAddress(Base):
    firstName: str | None = ''
    lastName: str | None = ''
    company: str | None = ''
    address1: str | None = ''
    address2: str | None = ''
    province: str | None = ''
    country: str | None = ''
    city: str | None = ''
    phone: str | None = ''
    zip: int | None = 0


class Customer(Base):
    firstName: str | None = ''
    lastName: str | None = ''
    id: str | None = ''


class ShopMoney(Base):
    amount: str | None = ''
    currencyCode: str | None = ''


class OriginalPriceSet(Base):
    shopMoney: ShopMoney | None = ShopMoney()


class LineItem(Base):
    name: str | None = ''
    quantity: int | None = 0
    originalUnitPriceSet: OriginalPriceSet | None = OriginalPriceSet()
    sku: str | None = ''


class PageInfo(Base):
    endCursor: str | None = ''
    hasNextPage: bool | None = False


class LineItemsNodes(Base):
    nodes: list[LineItem] | None = []
    pageInfo: PageInfo | None = PageInfo()


class ShippingLine(Base):
    originalPriceSet: OriginalPriceSet | None = OriginalPriceSet()


class Transaction(Base):
    gateway: str | None = ''
    paymentId: str | None = ''


class App(Base):
    name: str | None = ''


class Order(Base):
    fullyPaid: bool | None = False
    email: str | None = ''
    number: int | None = 0
    createdAt: datetime | None = None
    app: App | None = App()
    customer: Customer | None = Customer()
    transactions: list[Transaction] | None = []
    billingAddress: BillingAddress | None = BillingAddress()
    shippingLine: ShippingLine | None = ShippingLine()
    lineItems: LineItemsNodes | None = LineItemsNodes()


class OrderData(Base):
    order: Order | None = Order()  # Cuando no se encuentra la orden la respuesta llega con order: null


class OrderResponse(Base):
    data: OrderData | None = OrderData()
