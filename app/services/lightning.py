"""
Lightning Network service via LDK Node Python bindings.
Handles Bolt12 offer payments for automated re-ordering.

NOTE: This module requires the `ldk-node` Python package.
It is stubbed out for Phase 1-4 and will be fully implemented in Phase 5.
"""

from app.utils import logger
from app.db import insert_row, update_row


class LightningService:
    """
    Wrapper around LDK Node for Bolt12 payments.

    In the MVP, this provides a simulated payment flow.
    Phase 5 will integrate the actual LDK Node Python bindings.
    """

    def __init__(self):
        self._node = None
        self._initialized = False

    async def initialize(self):
        """
        Initialize the LDK Node.
        Phase 5: Replace with actual LDK Node initialization.
        """
        logger.info("Lightning service initializing (stub mode)...")
        # Phase 5: Uncomment and implement
        # from ldk_node import Builder, Network
        # builder = Builder.from_config(config)
        # builder.set_network(Network.TESTNET)
        # builder.set_esplora_server(settings.ldk_esplora_url)
        # builder.set_storage_dir_path(settings.ldk_storage_dir)
        # self._node = builder.build()
        # self._node.start()
        self._initialized = True
        logger.info("Lightning service ready (stub mode)")

    async def pay_bolt12_offer(
        self,
        duka_id: str,
        bolt12_offer: str,
        amount_sats: int,
        description: str = "Kiosk-GPT reorder",
    ) -> dict:
        """
        Pay a Bolt12 offer for automated re-ordering.

        Args:
            duka_id: The shop initiating the payment.
            bolt12_offer: The wholesaler's Bolt12 offer string.
            amount_sats: Amount in satoshis to pay.
            description: Payment description.

        Returns:
            Payment result dict with hash and status.
        """
        logger.info(f"Processing Bolt12 payment: {amount_sats} sats to offer {bolt12_offer[:20]}...")

        # Record the payment attempt
        payment_data = {
            "duka_id": duka_id,
            "payment_type": "reorder",
            "amount_sats": amount_sats,
            "bolt12_offer": bolt12_offer,
            "status": "pending",
        }
        payment_record = await insert_row("payments", payment_data)
        payment_id = payment_record.get("id")

        try:
            # Phase 5: Replace with actual LDK payment
            # offer = Offer.from_str(bolt12_offer)
            # payment_id = self._node.bolt12_payment().send(offer, amount_sats)
            # Wait for payment confirmation...

            # Stub: Simulate successful payment
            import hashlib
            import time
            fake_hash = hashlib.sha256(f"{bolt12_offer}{time.time()}".encode()).hexdigest()
            fake_preimage = hashlib.sha256(fake_hash.encode()).hexdigest()

            # Update payment record
            await update_row(
                "payments",
                {"id": payment_id},
                {
                    "payment_hash": fake_hash,
                    "payment_preimage": fake_preimage,
                    "status": "completed",
                },
            )

            logger.info(f"Payment completed: {fake_hash[:16]}...")
            return {
                "success": True,
                "payment_hash": fake_hash,
                "payment_preimage": fake_preimage,
                "amount_sats": amount_sats,
                "status": "completed",
            }

        except Exception as e:
            logger.error(f"Payment failed: {e}")
            await update_row("payments", {"id": payment_id}, {"status": "failed"})
            return {
                "success": False,
                "error": str(e),
                "amount_sats": amount_sats,
                "status": "failed",
            }

    async def get_node_info(self) -> dict:
        """Get node public info."""
        if not self._initialized:
            return {"status": "not_initialized"}

        # Phase 5: Return actual node info
        return {
            "status": "stub_mode",
            "node_id": "stub_node_id",
            "network": "testnet",
        }

    async def shutdown(self):
        """Gracefully shut down the LDK Node."""
        if self._node:
            # self._node.stop()
            pass
        self._initialized = False
        logger.info("Lightning service shut down")


# Singleton instance
lightning_service = LightningService()
