from __future__ import annotations
from dataclasses import dataclass
from typing import Dict

from schema.payments import (
    Payment,
    PaymentGateway,
    PaymentStatus,
    TransactionStatus,
)


@dataclass
class GatewayInitiation:
    payment_url: str
    external_reference: str


@dataclass
class GatewayStatus:
    payment_status: PaymentStatus
    transaction_status: TransactionStatus


class PaymentGatewayAdapter:
    """Adapter base para traducir nuestra API a distintos gateways."""

    gateway: PaymentGateway = PaymentGateway.MERCADOPAGO

    def initiate(self, payment: Payment) -> GatewayInitiation:
        raise NotImplementedError

    def normalize_status(self, raw_status: str) -> GatewayStatus:
        raise NotImplementedError


class MockMercadoPagoAdapter(PaymentGatewayAdapter):
    gateway = PaymentGateway.MERCADOPAGO

    def initiate(self, payment: Payment) -> GatewayInitiation:
        ref = payment.external_reference or ""
        url = f"https://mock.mercadopago.com/checkout?external_reference={ref}"
        return GatewayInitiation(payment_url=url, external_reference=ref)

    def normalize_status(self, raw_status: str) -> GatewayStatus:
        status = raw_status.lower()
        if status in {"approved", "success", "approved_by_gateway"}:
            return GatewayStatus(PaymentStatus.COMPLETED, TransactionStatus.APPROVED)
        if status in {"rejected", "failed", "declined"}:
            return GatewayStatus(PaymentStatus.FAILED, TransactionStatus.REJECTED)
        if status in {"pending", "in_process"}:
            return GatewayStatus(PaymentStatus.PENDING, TransactionStatus.PENDING)
        return GatewayStatus(PaymentStatus.PENDING, TransactionStatus.OTHER)


class MockCardAdapter(PaymentGatewayAdapter):
    def __init__(self, gateway: PaymentGateway, base_url: str):
        self.gateway = gateway
        self._base_url = base_url

    def initiate(self, payment: Payment) -> GatewayInitiation:
        ref = payment.external_reference or ""
        url = f"{self._base_url}/pay?token={ref}"
        return GatewayInitiation(payment_url=url, external_reference=ref)

    def normalize_status(self, raw_status: str) -> GatewayStatus:
        status = raw_status.lower()
        if status in {"authorized", "approved"}:
            return GatewayStatus(PaymentStatus.COMPLETED, TransactionStatus.APPROVED)
        if status in {"denied", "rejected"}:
            return GatewayStatus(PaymentStatus.FAILED, TransactionStatus.REJECTED)
        if status in {"review", "pending"}:
            return GatewayStatus(PaymentStatus.PENDING, TransactionStatus.PENDING)
        return GatewayStatus(PaymentStatus.PENDING, TransactionStatus.OTHER)


class MockTransferAdapter(PaymentGatewayAdapter):
    gateway = PaymentGateway.TRANSFER

    def initiate(self, payment: Payment) -> GatewayInitiation:
        ref = payment.external_reference or ""
        url = f"https://mock.transfer/checkout?ref={ref}"
        return GatewayInitiation(payment_url=url, external_reference=ref)

    def normalize_status(self, raw_status: str) -> GatewayStatus:
        status = raw_status.lower()
        if status in {"credited", "confirmed"}:
            return GatewayStatus(PaymentStatus.COMPLETED, TransactionStatus.APPROVED)
        if status in {"returned", "cancelled"}:
            return GatewayStatus(PaymentStatus.FAILED, TransactionStatus.REJECTED)
        return GatewayStatus(PaymentStatus.PENDING, TransactionStatus.PENDING)


def _build_adapters() -> Dict[PaymentGateway, PaymentGatewayAdapter]:
    return {
        PaymentGateway.MERCADOPAGO: MockMercadoPagoAdapter(),
        PaymentGateway.CREDIT_CARD: MockCardAdapter(PaymentGateway.CREDIT_CARD, "https://mock.credit"),
        PaymentGateway.DEBIT_CARD: MockCardAdapter(PaymentGateway.DEBIT_CARD, "https://mock.debit"),
        PaymentGateway.TRANSFER: MockTransferAdapter(),
    }


_ADAPTERS = _build_adapters()


def get_gateway_adapter(gateway: PaymentGateway | None) -> PaymentGatewayAdapter:
    if gateway and gateway in _ADAPTERS:
        return _ADAPTERS[gateway]
    return _ADAPTERS[PaymentGateway.MERCADOPAGO]
