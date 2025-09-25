App
## Finance AI Backend (Plaid + Prisma + Express)

### Prerequisites
- Node.js >= 18

### Setup
1. Copy env file:
   - `cp .env.example .env`
2. Fill `PLAID_CLIENT_ID` and `PLAID_SECRET` (use Sandbox keys for testing).
3. Install dependencies:
   - `npm install`
4. Generate Prisma client and create DB:
   - `npx prisma generate`
   - `npx prisma migrate dev --name init`

### Run
- Dev: `npm run dev`
- Build: `npm run build`
- Start: `npm start`

### API
- `GET /health` -> `{ ok: true }`
- `POST /api/plaid/link-token/create` body: `{ userId }` -> `{ link_token }`
- `POST /api/plaid/token/exchange` body: `{ userId, public_token }` -> `{ ok, itemId }`
- `POST /api/transactions/sync` body: `{ userId }` -> `{ ok, counts }`
- `GET /api/accounts?userId=...` -> `{ accounts }`
- `GET /api/transactions?userId=...` -> `{ transactions }`
