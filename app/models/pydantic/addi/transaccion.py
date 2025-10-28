from datetime import datetime
from typing import Any
from app.models.pydantic.base import Base


class Transaction(Base):
    transactionId: str | None = None
    nationalIdType: str | None = None
    nationalIdNumber: float | None = None
    clientName: str | None = None
    amount: float | None = None
    amountWithDiscount: float | None = None
    discount: float | None = None
    addiDiscountPercentageAssumed: float | None = None
    addiDiscountPercentage: float | None = None
    addiDiscountAmount: float | None = None
    allyDiscountPercentageAssumed: float | None = None
    allyDiscountAmount: float | None = None
    allyDiscountPercentage: float | None = None
    createdAt: datetime | None = None
    allyName: str | None = None
    allySLug: str | None = None
    storeName: str | None = None
    storeSlug: str | None = None
    storeUserEmail: str | None = None
    loanId: str | None = None
    channel: str | None = None
    status: str | None = None
    stage: str | None = None
    funderName: str | None = None
    paymentType: str | None = None
    cancellationId: str | None = None
    cancellationReason: str | None = None
    cancellationCreatedAt: str | None = None
    cancellationUserName: str | None = None
    journey: str | None = None
    orderId: str | None = None
    cancellations: list[Any] = []
    allCancellations: list[Any] = []


class TransactionsResponse(Base):
    transactions: list[Transaction] = []
    pagination: str | None = None
