const numberFromEnv = (value, fallback) => {
    const parsed = value ? parseInt(value, 10) : NaN;
    return Number.isFinite(parsed) ? parsed : fallback;
};
const config = {
    port: numberFromEnv(process.env.PORT, 3000),
    sessionSecret: process.env.SESSION_SECRET || 'devsecret',
    plaid: {
        env: (process.env.PLAID_ENV || 'sandbox'),
        clientId: process.env.PLAID_CLIENT_ID || '',
        secret: process.env.PLAID_SECRET || '',
        redirectUri: process.env.PLAID_REDIRECT_URI,
    },
    db: {
        url: process.env.DATABASE_URL || 'file:./prisma/dev.db',
    },
};
export default config;
