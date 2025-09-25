# Finance Aggregator + AI Backend (Node + TypeScript)

This service connects to supported financial institutions via Plaid, fetches accounts and transactions, and stores them in a local SQLite DB (Prisma) for downstream AI analysis.

## Quickstart

1) Install deps

```bash
npm install
```

2) Configure env

Copy `.env.example` to `.env` and set your Plaid credentials:

```bash
cp .env.example .env
# Edit .env: PLAID_CLIENT_ID, PLAID_SECRET, PLAID_ENV, etc
```

3) Run database migrations

```bash
npx prisma migrate dev
```

4) Start in dev

```bash
npm run dev
```

Or build and run:

```bash
npm run build
npm start
```

## Environment Variables

- `DATABASE_URL` (default `file:./dev.db`)
- `PORT` (default `3000`)
- `PLAID_ENV` (`sandbox` | `development` | `production`)
- `PLAID_CLIENT_ID`
- `PLAID_SECRET`
- `PLAID_PRODUCTS` (comma list, default `transactions`)
- `PLAID_COUNTRY_CODES` (comma list, default `US`)
- `PLAID_REDIRECT_URI` (optional)

## API

- `POST /users` -> create/upsert a user
  - body: `{ "email": "user@example.com" }`
- `POST /plaid/link-token` -> create a Link token for a user
  - body: `{ "userId": "<user-id>" }`
- `POST /plaid/exchange` -> exchange `public_token` for `access_token`, save connection
  - body: `{ "userId": "<user-id>", "publicToken": "<token>" }`
- `GET /connections/:id/accounts` -> list accounts from DB
- `GET /accounts/:id/transactions` -> list transactions from DB
- `POST /api/connections/:id/sync` -> trigger transactions sync for a connection
- `POST /api/connections/:id/refresh-accounts` -> refresh accounts from Plaid
- `POST /webhook/plaid` -> Plaid webhook (logs payload)

## Data Model (Prisma)

- `User` -> basic user record
- `Connection` -> a Plaid item per user
- `Account` -> financial accounts under a connection
- `Transaction` -> transactions tied to an account
- `SyncCursor` -> stores `transactionsSync` cursor per connection

Inspect or modify via Prisma Studio:

```bash
npx prisma studio
```

## Developing

- Type check and build: `npm run build`
- Prisma client regen when schema changes: `npx prisma generate`
- Migrations: `npx prisma migrate dev --name <name>`

## Notes

- This backend does not include a UI. Use Plaid Link in your frontend to obtain a `public_token` and call `/plaid/exchange`.
- SQLite is great for local dev. For production, switch `datasource` in `prisma/schema.prisma` to Postgres or MySQL and update `DATABASE_URL`.
