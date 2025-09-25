import express from 'express';
import { z } from 'zod';
import { plaidClient, Products, CountryCode } from '../plaid.js';
import { prisma } from '../db.js';

const router = express.Router();

const CreateLinkTokenSchema = z.object({
  userId: z.string().min(1),
});

router.post('/plaid/link-token/create', async (req, res) => {
  try {
    const { userId } = CreateLinkTokenSchema.parse(req.body);

    const response = await plaidClient.linkTokenCreate({
      user: { client_user_id: userId },
      client_name: 'Finance AI App',
      products: [Products.Transactions],
      country_codes: [CountryCode.Us],
      language: 'en',
      redirect_uri: process.env.PLAID_REDIRECT_URI || undefined,
    });

    res.json({ link_token: response.data.link_token });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Failed to create link token' });
  }
});

const ExchangePublicTokenSchema = z.object({
  userId: z.string().min(1),
  public_token: z.string().min(1),
});

router.post('/plaid/token/exchange', async (req, res) => {
  try {
    const { userId, public_token } = ExchangePublicTokenSchema.parse(req.body);

    // Ensure user exists
    await prisma.user.upsert({
      where: { id: userId },
      update: {},
      create: { id: userId },
    });

    const exchange = await plaidClient.itemPublicTokenExchange({ public_token });
    const accessToken = exchange.data.access_token;
    const plaidItemId = exchange.data.item_id;

    // Fetch institution and accounts
    const accounts = await plaidClient.accountsGet({ access_token: accessToken });

    const institutionId = accounts.data.item?.institution_id || undefined;

    // Create Item
    const item = await prisma.item.upsert({
      where: { plaidItemId },
      update: { accessToken, institutionId, userId },
      create: { userId, plaidItemId, accessToken, institutionId },
    });

    // Upsert Accounts
    const upserts = accounts.data.accounts.map((acct) =>
      prisma.account.upsert({
        where: { plaidAccountId: acct.account_id },
        update: {
          itemId: item.id,
          name: acct.name || null,
          officialName: acct.official_name || null,
          mask: acct.mask || null,
          type: acct.type || null,
          subtype: acct.subtype || null,
          availableBalance: acct.balances.available != null ? acct.balances.available : null,
          currentBalance: acct.balances.current != null ? acct.balances.current : null,
          currency: acct.balances.iso_currency_code || 'USD',
        },
        create: {
          itemId: item.id,
          plaidAccountId: acct.account_id,
          name: acct.name || null,
          officialName: acct.official_name || null,
          mask: acct.mask || null,
          type: acct.type || null,
          subtype: acct.subtype || null,
          availableBalance: acct.balances.available != null ? acct.balances.available : null,
          currentBalance: acct.balances.current != null ? acct.balances.current : null,
          currency: acct.balances.iso_currency_code || 'USD',
        },
      })
    );

    await prisma.$transaction(upserts);

    res.json({ ok: true, itemId: item.id });
  } catch (err: any) {
    res.status(400).json({ error: err.message || 'Failed to exchange token' });
  }
});

export default router;

