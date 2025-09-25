import { PrismaClient } from '@prisma/client';
import { plaid } from './plaid.js';
import { config } from './config.js';

const prisma = new PrismaClient();

export async function syncConnection(connectionId: string): Promise<void> {
  const connection = await prisma.connection.findUnique({ where: { id: connectionId } });
  if (!connection) return;

  // 1) Sync accounts
  try {
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
  } catch (err) {
    console.error('accountsGet failed', err);
  }

  // 2) Transactions sync loop
  let cursor: string | null = null;
  const existingCursor = await prisma.syncCursor.findUnique({ where: { connectionId: connection.id } });
  if (existingCursor) cursor = existingCursor.cursor ?? null;

  let hasMore = true;
  while (hasMore) {
    const req: any = { access_token: connection.accessToken, count: 500 };
    if (cursor !== null) req.cursor = cursor;
    const resp = await plaid.transactionsSync(req);

    // Added transactions
    for (const t of resp.data.added) {
      await prisma.transaction.upsert({
        where: { transactionId: t.transaction_id },
        update: {
          accountId: t.account_id,
          amount: t.amount,
          isoCurrencyCode: (t.iso_currency_code ?? 'USD'),
          merchantName: t.merchant_name ?? null,
          name: t.name ?? null,
          date: new Date(t.date),
          pending: Boolean(t.pending),
          categoryPrimary: t.personal_finance_category?.primary ?? null,
          categoryDetailed: t.personal_finance_category?.detailed ?? null,
          paymentChannel: t.payment_channel ?? null,
          authorizedDate: t.authorized_date ? new Date(t.authorized_date) : null,
        },
        create: {
          accountId: t.account_id,
          transactionId: t.transaction_id,
          amount: t.amount,
          isoCurrencyCode: (t.iso_currency_code ?? 'USD'),
          merchantName: t.merchant_name ?? null,
          name: t.name ?? null,
          date: new Date(t.date),
          pending: Boolean(t.pending),
          categoryPrimary: t.personal_finance_category?.primary ?? null,
          categoryDetailed: t.personal_finance_category?.detailed ?? null,
          paymentChannel: t.payment_channel ?? null,
          authorizedDate: t.authorized_date ? new Date(t.authorized_date) : null,
        },
      });
    }

    // Modified transactions
    for (const t of resp.data.modified) {
      await prisma.transaction.update({
        where: { transactionId: t.transaction_id },
        data: {
          accountId: t.account_id,
          amount: t.amount,
          isoCurrencyCode: (t.iso_currency_code ?? 'USD'),
          merchantName: t.merchant_name ?? null,
          name: t.name ?? null,
          date: new Date(t.date),
          pending: Boolean(t.pending),
          categoryPrimary: t.personal_finance_category?.primary ?? null,
          categoryDetailed: t.personal_finance_category?.detailed ?? null,
          paymentChannel: t.payment_channel ?? null,
          authorizedDate: t.authorized_date ? new Date(t.authorized_date) : null,
        },
      });
    }

    // Removed transactions
    const removedIds = resp.data.removed.map(r => r.transaction_id);
    if (removedIds.length) {
      await prisma.transaction.deleteMany({ where: { transactionId: { in: removedIds } } });
    }

    // Update cursor
    cursor = resp.data.next_cursor ?? null;
    hasMore = resp.data.has_more ?? false;
  }

  await prisma.syncCursor.upsert({
    where: { connectionId: connection.id },
    update: { cursor },
    create: { connectionId: connection.id, cursor },
  });
}

export async function syncAllConnections(): Promise<void> {
  const connections = await prisma.connection.findMany();
  for (const c of connections) {
    await syncConnection(c.id);
  }
}