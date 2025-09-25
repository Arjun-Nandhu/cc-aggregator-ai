import express from 'express';
import cors from 'cors';
import pino from 'pino';
import pinoHttp from 'pino-http';
import { z } from 'zod';
import { config } from './config.js';
import { plaid } from './plaid.js';
import { PrismaClient } from '@prisma/client';
import { buildRouter } from './routes.js';

const app = express();
const logger = pino({ transport: { target: 'pino-pretty' } });
const prisma = new PrismaClient();

app.use(cors());
app.use(express.json());
app.use(pinoHttp({ logger }));

// Health
app.get('/health', (_req, res) => {
  res.json({ ok: true });
});

// Create a user (simple demo user creator)
app.post('/users', async (req, res) => {
  const schema = z.object({ email: z.string().email() });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const user = await prisma.user.upsert({
    where: { email: parsed.data.email },
    update: {},
    create: { email: parsed.data.email },
  });
  res.json(user);
});

// Create a Plaid Link token
app.post('/plaid/link-token', async (req, res) => {
  const schema = z.object({ userId: z.string() });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const user = await prisma.user.findUnique({ where: { id: parsed.data.userId } });
  if (!user) return res.status(404).json({ error: 'User not found' });
  try {
    const baseReq: any = {
      client_name: 'Finance AI Aggregator',
      language: 'en',
      user: { client_user_id: user.id },
      country_codes: config.plaidCountryCodes as any,
      products: config.plaidProducts as any,
    };
    if (config.plaidRedirectUri) baseReq.redirect_uri = config.plaidRedirectUri;
    const response = await plaid.linkTokenCreate(baseReq);
    res.json(response.data);
  } catch (err) {
    req.log.error({ err }, 'linkTokenCreate failed');
    res.status(500).json({ error: 'Failed to create link token' });
  }
});

// Exchange public_token for access_token and create Connection
app.post('/plaid/exchange', async (req, res) => {
  const schema = z.object({ userId: z.string(), publicToken: z.string() });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ error: parsed.error.flatten() });
  const user = await prisma.user.findUnique({ where: { id: parsed.data.userId } });
  if (!user) return res.status(404).json({ error: 'User not found' });
  try {
    const exchange = await plaid.itemPublicTokenExchange({ public_token: parsed.data.publicToken });
    const itemId = exchange.data.item_id;
    const accessToken = exchange.data.access_token;
    const item = await plaid.itemGet({ access_token: accessToken });
    const institutionId = item.data.item.institution_id ?? null;
    let institutionName: string | null = null;
    if (institutionId) {
      try {
        const inst = await plaid.institutionsGetById({ institution_id: institutionId, country_codes: config.plaidCountryCodes as any });
        institutionName = inst.data.institution.name ?? null;
      } catch {}
    }
    const connection = await prisma.connection.upsert({
      where: { itemId },
      update: { accessToken, institutionId, institutionName },
      create: { userId: user.id, provider: 'plaid', itemId, accessToken, institutionId, institutionName },
      include: { user: true },
    });
    res.json({ connectionId: connection.id, itemId });
  } catch (err) {
    req.log.error({ err }, 'publicTokenExchange failed');
    res.status(500).json({ error: 'Failed to exchange public token' });
  }
});

// List accounts for a connection (from DB)
app.get('/connections/:id/accounts', async (req, res) => {
  const connectionId = req.params.id;
  const connection = await prisma.connection.findUnique({ where: { id: connectionId } });
  if (!connection) return res.status(404).json({ error: 'Connection not found' });
  const accounts = await prisma.account.findMany({ where: { connectionId }, orderBy: { name: 'asc' } });
  res.json(accounts);
});

// List transactions for an account (from DB)
app.get('/accounts/:id/transactions', async (req, res) => {
  const accountId = req.params.id;
  const transactions = await prisma.transaction.findMany({ where: { accountId }, orderBy: { date: 'desc' }, take: 500 });
  res.json(transactions);
});

// Webhook endpoint (Plaid)
app.post('/webhook/plaid', async (req, res) => {
  req.log.info({ body: req.body }, 'Received Plaid webhook');
  res.status(200).json({ ok: true });
});

app.use('/api', buildRouter());

app.listen(config.port, () => {
  logger.info(`Server listening on :${config.port}`);
});

process.on('SIGINT', async () => {
  await prisma.$disconnect();
  process.exit(0);
});

