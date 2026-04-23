# 🏪 Kiosk-GPT

> **WhatsApp-native kiosk management for Kenyan shopkeepers — powered by AI + Lightning ⚡**

Kiosk-GPT lets small shop owners (duka operators) manage inventory, record sales, and make instant payments using nothing but WhatsApp — in Sheng, Swahili, or English.

## Architecture

```
WhatsApp ←→ FastAPI ←→ Groq (Llama 3.2) + Supabase + LDK Node
```

- **Frontend**: WhatsApp Cloud API + Flows (no custom app needed)
- **Backend**: Python FastAPI
- **AI**: Llama 3.2 via Groq (Sheng/Swahili → structured JSON)
- **Payments**: LDK Node with Bolt12 Offers (Lightning Network)
- **Database**: Supabase (Postgres + Realtime dashboard)

## Quick Start

```bash
# 1. Clone & enter
git clone https://github.com/your-username/kiosk-GPT.git
cd kiosk-GPT

# 2. Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
copy .env.example .env
# Edit .env with your actual keys

# 5. Run the server
uvicorn app.main:app --reload --port 8000
```

## User Flow

1. **Registration**: User sends "Hi" → gets a WhatsApp Flow form → fills in Duka name, type, Lightning address
2. **Record Sale**: User sends "Nimeuza mkate tatu na maziwa mbao" → AI parses → stock updated → confirmation sent
3. **Re-order**: Low stock alert → user taps "Yes, Re-order" → Lightning payment → receipt sent

## Project Structure

```
app/
├── main.py              # FastAPI entrypoint
├── config.py            # Environment configuration
├── api/                 # Route handlers (webhooks, flows, health)
├── services/            # Business logic (WhatsApp, AI, inventory, Lightning)
├── models/              # Pydantic models
├── db/                  # Supabase client
└── utils/               # Logging, constants
```

## License

MIT
