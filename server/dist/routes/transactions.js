import express from 'express';
import { z } from 'zod';
import { prisma } from '../db.js';
import { plaidClient } from '../plaid.js';
const router = express.Router();
const SyncSchema = z.object({ userId: z.string().min(1) });
router.post('/transactions/sync', async (req, res) => {
    try {
        const { userId } = SyncSchema.parse(req.body);
        const items = await prisma.item.findMany({ where: { userId } });
        let addedTotal = 0;
        let modifiedTotal = 0;
        let removedTotal = 0;
        for (const item of items) {
            let cursor = item.transactionsCursor ?? undefined;
            let hasMore = true;
            while (hasMore) {
                const resp = await plaidClient.transactionsSync({
                    access_token: item.accessToken,
                    cursor,
                });
                const added = resp.data.added || [];
                const modified = resp.data.modified || [];
                const removed = resp.data.removed || [];
                // Upsert added
                const addOps = added.map((tx) => prisma.transaction.upsert({
                    where: { plaidTransactionId: tx.transaction_id },
                    create: {
                        account: { connect: { plaidAccountId: tx.account_id } },
                        plaidTransactionId: tx.transaction_id,
                        name: tx.name || null,
                        merchantName: tx.merchant_name || null,
                        amount: tx.amount,
                        isoCurrencyCode: tx.iso_currency_code || 'USD',
                        date: new Date(tx.date),
                        authorizedDate: tx.authorized_date ? new Date(tx.authorized_date) : null,
                        pending: Boolean(tx.pending),
                        category: tx.category ?? undefined,
                        location: tx.location ?? undefined,
                        paymentChannel: tx.payment_channel || null,
                    },
                    update: {
                        name: tx.name || null,
                        merchantName: tx.merchant_name || null,
                        amount: tx.amount,
                        isoCurrencyCode: tx.iso_currency_code || 'USD',
                        date: new Date(tx.date),
                        authorizedDate: tx.authorized_date ? new Date(tx.authorized_date) : null,
                        pending: Boolean(tx.pending),
                        category: tx.category ?? undefined,
                        location: tx.location ?? undefined,
                        paymentChannel: tx.payment_channel || null,
                    },
                }));
                const modOps = modified.map((tx) => prisma.transaction.update({
                    where: { plaidTransactionId: tx.transaction_id },
                    data: {
                        name: tx.name || null,
                        merchantName: tx.merchant_name || null,
                        amount: tx.amount,
                        isoCurrencyCode: tx.iso_currency_code || 'USD',
                        date: new Date(tx.date),
                        authorizedDate: tx.authorized_date ? new Date(tx.authorized_date) : null,
                        pending: Boolean(tx.pending),
                        category: tx.category ?? undefined,
                        location: tx.location ?? undefined,
                        paymentChannel: tx.payment_channel || null,
                    },
                }));
                const delOps = removed.map((tx) => prisma.transaction.deleteMany({ where: { plaidTransactionId: tx.transaction_id } }));
                await prisma.$transaction([...addOps, ...modOps, ...delOps]);
                addedTotal += added.length;
                modifiedTotal += modified.length;
                removedTotal += removed.length;
                cursor = resp.data.next_cursor ?? cursor;
                hasMore = Boolean(resp.data.has_more);
            }
            await prisma.item.update({
                where: { id: item.id },
                data: { transactionsCursor: cursor },
            });
        }
        res.json({ ok: true, counts: { added: addedTotal, modified: modifiedTotal, removed: removedTotal } });
    }
    catch (err) {
        res.status(400).json({ error: err.message || 'Sync failed' });
    }
});
const ListSchema = z.object({ userId: z.string().min(1) });
router.get('/accounts', async (req, res) => {
    try {
        const { userId } = ListSchema.parse(req.query);
        const accounts = await prisma.account.findMany({
            where: { item: { userId: String(userId) } },
            orderBy: { createdAt: 'desc' },
        });
        res.json({ accounts });
    }
    catch (err) {
        res.status(400).json({ error: err.message || 'Failed to list accounts' });
    }
});
router.get('/transactions', async (req, res) => {
    try {
        const { userId } = ListSchema.parse(req.query);
        const txs = await prisma.transaction.findMany({
            where: { account: { item: { userId: String(userId) } } },
            orderBy: { date: 'desc' },
            take: 500,
        });
        res.json({ transactions: txs });
    }
    catch (err) {
        res.status(400).json({ error: err.message || 'Failed to list transactions' });
    }
});
export default router;
