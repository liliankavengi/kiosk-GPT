# Production Readiness for Kiosk-GPT

Implement the remaining core features, security patches, and payment services to prepare Kiosk-GPT for live production use by Kenyan shopkeepers.

## User Review Required

> [!IMPORTANT]
> **Hosted Lightning API over LDK Node:**
> Running a local self-custodial `ldk-node` in container environments like Railway requires persistent storage, static IPs, and complex channel liquidity management. For production readiness and stability, we propose integrating **LNbits** or **Alby** API as the primary production Lightning payment gateway, while retaining a modular interface so developers can swap in LDK Node later if desired.

> [!IMPORTANT]
> **RSA Keypair for WhatsApp Flows:**
> Decrypting Flow data requires generating an RSA public/private keypair. The public key must be uploaded to the Meta App Settings dashboard, and the private key must be configured in Kiosk-GPT settings (`WHATSAPP_FLOW_PRIVATE_KEY`).

---

## Proposed Changes

### Dependency Configuration

#### [MODIFY] [requirements.txt](file:///c:/Users/kaven/kiosk-GPT/requirements.txt)
- Add `cryptography>=42.0.0` for AES-GCM and RSA decryption/encryption of WhatsApp Flow payloads.

---

### Core Settings and Cryptography

#### [MODIFY] [app/config.py](file:///c:/Users/kaven/kiosk-GPT/app/config.py)
- Add `whatsapp_app_secret` for webhook signature verification.
- Add `whatsapp_flow_private_key` (PEM string or file path) for decrypting Flows.
- Add `lightning_provider` (values: `stub`, `lnbits`), `lnbits_url`, and `lnbits_api_key`.

#### [NEW] [app/utils/crypto.py](file:///c:/Users/kaven/kiosk-GPT/app/utils/crypto.py)
- Implement `FlowCrypter` class to decrypt and encrypt Meta Flows payloads using AES-GCM-128/256 and RSA-OAEP.
- Implement helper function to verify `X-Hub-Signature-256` webhook signatures.

---

### Route Logic & Webhook Security

#### [MODIFY] [app/api/webhooks.py](file:///c:/Users/kaven/kiosk-GPT/app/api/webhooks.py)
- Add middleware or a decorator to verify `X-Hub-Signature-256` signature using raw body and the configured `whatsapp_app_secret`.
- Integrate PDF media upload to WhatsApp API on successful payments.

#### [MODIFY] [app/api/flows.py](file:///c:/Users/kaven/kiosk-GPT/app/api/flows.py)
- Update data exchange route to automatically decrypt the incoming request payload using `FlowCrypter` if decryption settings are provided, and encrypt the response before sending it back to Meta.

---

### External Services & Deliveries

#### [MODIFY] [app/services/whatsapp.py](file:///c:/Users/kaven/kiosk-GPT/app/services/whatsapp.py)
- Add `upload_media` method to upload PDF receipt bytes to Meta's `/media` endpoint.
- Enhance `send_document` to support sending document media using the native `media_id` returned by the upload API.

#### [MODIFY] [app/services/lightning.py](file:///c:/Users/kaven/kiosk-GPT/app/services/lightning.py)
- Implement active LNbits payment client to pay Bolt12 or LNURL invoices dynamically for stock reorders.

---

### User Dashboard & Setup Automation

#### [NEW] [dashboard/index.html](file:///c:/Users/kaven/kiosk-GPT/dashboard/index.html)
- Create a web dashboard showing realtime inventory state, sales logs, and payment states.

#### [NEW] [dashboard/style.css](file:///c:/Users/kaven/kiosk-GPT/dashboard/style.css)
- Add vanilla CSS rules for the dashboard styling.

#### [NEW] [dashboard/app.js](file:///c:/Users/kaven/kiosk-GPT/dashboard/app.js)
- Implement Supabase Realtime subscriptions to update UI tables automatically on database operations.

#### [NEW] [scripts/setup_whatsapp.py](file:///c:/Users/kaven/kiosk-GPT/scripts/setup_whatsapp.py)
- Script to upload the flow JSON configuration to Meta Business Accounts.

---

## Verification Plan

### Automated Tests
- Run `pytest` to verify existing model validations:
  ```powershell
  venv/Scripts/pytest.exe -v
  ```
- Write new unit tests in [tests/test_crypto.py](file:///c:/Users/kaven/kiosk-GPT/tests/test_crypto.py) to validate HMAC signature verification and flow encryption/decryption roundtrips.

### Manual Verification
- Test signature validation locally by simulating requests with valid and invalid HMAC headers.
- Verify receipt generation and document dispatch with test WhatsApp credentials.
