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
    admin_graphql_api_id: str = ''  # Webhook con guiones bajos


class BillingAddress(Base):
    firstName: str = ''
    lastName: str = ''
    company: str = ''
    address1: str = ''
    address2: str = ''
    province: str = ''
    country: str = ''
    city: str = ''
    phone: str = ''
    zip: int = 0


class Customer(Base):
    firstName: str = ''
    lastName: str = ''
    id: str = ''


class ShopMoney(Base):
    amount: str = ''
    currencyCode: str = ''


class OriginalPriceSet(Base):
    shopMoney: ShopMoney = ShopMoney()


class LineItem(Base):
    name: str = ''
    quantity: int = 0
    originalUnitPriceSet: OriginalPriceSet = OriginalPriceSet()
    sku: str = ''


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
    createdAt: datetime | None = None
    app: App = App()
    customer: Customer = Customer()
    transactions: list[Transaction] = []
    billingAddress: BillingAddress = BillingAddress()
    shippingLine: ShippingLine = ShippingLine()
    lineItems: LineItemsNodes = LineItemsNodes()


class OrderData(Base):
    order: Order | None = Order()  # Cuando no se encuentra la orden la respuesta llega con order: null


class OrderResponse(Base):
    data: OrderData = OrderData()
