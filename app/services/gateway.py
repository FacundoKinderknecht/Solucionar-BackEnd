"""Payment gateway adapter layer.

Provides a uniform interface for multiple payment gateways through the
Adapter pattern. All concrete implementations are mocks used for development.
Replace with real SDK integrations before going to production.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.models.payment import Payment, PaymentGateway, PaymentStatus, TransactionStatus


@dataclass
class GatewayInitiation:
    """Result of initiating a payment checkout session."""

    payment_url: str
    external_reference: str


@dataclass
class GatewayStatus:
    """Normalised payment and transaction statuses returned by a gateway."""

    payment_status: PaymentStatus
    transaction_status: TransactionStatus


class PaymentGatewayAdapter:
    """Abstract base adapter — subclass and implement both methods for each gateway."""

    gateway: PaymentGateway = PaymentGateway.MERCADOPAGO

    def initiate(self, payment: Payment) -> GatewayInitiation:
        """Initiate a checkout session and return the redirect URL.

        Args:
            payment: The ``Payment`` record to initiate.

        Returns:
            A ``GatewayInitiation`` with the checkout URL and reference.
        """
        raise NotImplementedError

    def normalize_status(self, raw_status: str) -> GatewayStatus:
        """Map a raw gateway status string to domain enums.

        Args:
            raw_status: Status string returned by the gateway webhook.

        Returns:
            A ``GatewayStatus`` with normalised ``PaymentStatus`` and
            ``TransactionStatus`` values.
        """
        raise NotImplementedError


class MockMercadoPagoAdapter(PaymentGatewayAdapter):
    """Mock adapter for MercadoPago — returns static URLs for local development."""

    gateway = PaymentGateway.MERCADOPAGO

    def initiate(self, payment: Payment) -> GatewayInitiation:
        """Return a mock MercadoPago checkout URL."""
        ref = payment.external_reference or ""
        return GatewayInitiation(
            payment_url=f"https://mock.mercadopago.com/checkout?external_reference={ref}",
            external_reference=ref,
        )

    def normalize_status(self, raw_status: str) -> GatewayStatus:
        """Map MercadoPago status strings to domain enums."""
        s = raw_status.lower()
        if s in {"approved", "success", "approved_by_gateway"}:
            return GatewayStatus(PaymentStatus.COMPLETED, TransactionStatus.APPROVED)
        if s in {"rejected", "failed", "declined"}:
            return GatewayStatus(PaymentStatus.FAILED, TransactionStatus.REJECTED)
        if s in {"pending", "in_process"}:
            return GatewayStatus(PaymentStatus.PENDING, TransactionStatus.PENDING)
        return GatewayStatus(PaymentStatus.PENDING, TransactionStatus.OTHER)


class MockCardAdapter(PaymentGatewayAdapter):
    """Mock adapter for credit/debit card gateways."""

    def __init__(self, gateway: PaymentGateway, base_url: str) -> None:
        """Initialise with the gateway identifier and mock base URL."""
        self.gateway = gateway
        self._base_url = base_url

    def initiate(self, payment: Payment) -> GatewayInitiation:
        """Return a mock card checkout URL."""
        ref = payment.external_reference or ""
        return GatewayInitiation(
            payment_url=f"{self._base_url}/pay?token={ref}",
            external_reference=ref,
        )

    def normalize_status(self, raw_status: str) -> GatewayStatus:
        """Map card gateway status strings to domain enums."""
        s = raw_status.lower()
        if s in {"authorized", "approved"}:
            return GatewayStatus(PaymentStatus.COMPLETED, TransactionStatus.APPROVED)
        if s in {"denied", "rejected"}:
            return GatewayStatus(PaymentStatus.FAILED, TransactionStatus.REJECTED)
        if s in {"review", "pending"}:
            return GatewayStatus(PaymentStatus.PENDING, TransactionStatus.PENDING)
        return GatewayStatus(PaymentStatus.PENDING, TransactionStatus.OTHER)


class MockTransferAdapter(PaymentGatewayAdapter):
    """Mock adapter for bank transfer payments."""

    gateway = PaymentGateway.TRANSFER

    def initiate(self, payment: Payment) -> GatewayInitiation:
        """Return a mock transfer checkout URL."""
        ref = payment.external_reference or ""
        return GatewayInitiation(
            payment_url=f"https://mock.transfer/checkout?ref={ref}",
            external_reference=ref,
        )

    def normalize_status(self, raw_status: str) -> GatewayStatus:
        """Map bank transfer status strings to domain enums."""
        s = raw_status.lower()
        if s in {"credited", "confirmed"}:
            return GatewayStatus(PaymentStatus.COMPLETED, TransactionStatus.APPROVED)
        if s in {"returned", "cancelled"}:
            return GatewayStatus(PaymentStatus.FAILED, TransactionStatus.REJECTED)
        return GatewayStatus(PaymentStatus.PENDING, TransactionStatus.PENDING)


_ADAPTERS: dict[PaymentGateway, PaymentGatewayAdapter] = {
    PaymentGateway.MERCADOPAGO: MockMercadoPagoAdapter(),
    PaymentGateway.CREDIT_CARD: MockCardAdapter(
        PaymentGateway.CREDIT_CARD, "https://mock.credit"
    ),
    PaymentGateway.DEBIT_CARD: MockCardAdapter(
        PaymentGateway.DEBIT_CARD, "https://mock.debit"
    ),
    PaymentGateway.TRANSFER: MockTransferAdapter(),
}


def get_gateway_adapter(gateway: PaymentGateway | None) -> PaymentGatewayAdapter:
    """Return the adapter for the given gateway, falling back to MercadoPago.

    Args:
        gateway: The payment gateway identifier.

    Returns:
        The matching ``PaymentGatewayAdapter`` instance.
    """
    if gateway and gateway in _ADAPTERS:
        return _ADAPTERS[gateway]
    return _ADAPTERS[PaymentGateway.MERCADOPAGO]
