import { Router } from 'express';
import { z } from 'zod';
import { PrismaClient } from '@prisma/client';
import { plaid } from './plaid.js';
import { config } from './config.js';
import { syncConnection } from './sync.js';

const prisma = new PrismaClient();

export function buildRouter(): Router {
  const r = Router();

  // Trigger manual sync for a connection
  r.post('/connections/:id/sync', async (req, res) => {
    const id = req.params.id;
    const conn = await prisma.connection.findUnique({ where: { id } });
    if (!conn) return res.status(404).json({ error: 'Connection not found' });
    await syncConnection(id);
    res.json({ ok: true });
  });

  // Fetch fresh accounts from Plaid and refresh DB
  r.post('/connections/:id/refresh-accounts', async (req, res) => {
    const id = req.params.id;
    const connection = await prisma.connection.findUnique({ where: { id } });
    if (!connection) return res.status(404).json({ error: 'Connection not found' });
    const accountsResp = await plaid.accountsGet({ access_token: connection.accessToken });
    const accounts = accountsResp.data.accounts;
    for (const a of accounts) {
      await prisma.account.upsert({
        where: { accountId: a.account_id },
        update: {
          connectionId: connection.id,
          mask: a.mask ?? null,
          name: a.name ?? a.official_name ?? 'Account',
          officialName: a.official_name ?? null,
          type: a.type ?? 'other',
          subtype: a.subtype ?? null,
          currentBalance: a.balances.current ?? null,
          availableBalance: a.balances.available ?? null,
          currency: a.balances.iso_currency_code ?? 'USD',
        },
        create: {
          connectionId: connection.id,
          accountId: a.account_id,
          mask: a.mask ?? null,
          name: a.name ?? a.official_name ?? 'Account',
          officialName: a.official_name ?? null,
          type: a.type ?? 'other',
          subtype: a.subtype ?? null,
          currentBalance: a.balances.current ?? null,
          availableBalance: a.balances.available ?? null,
          currency: a.balances.iso_currency_code ?? 'USD',
        },
      });
    }
    res.json({ count: accounts.length });
  });

  return r;
}

