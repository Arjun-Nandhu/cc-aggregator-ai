import './env.js';
import express from 'express';
import session from 'express-session';
import helmet from 'helmet';
import morgan from 'morgan';
import cors from 'cors';
import config from './config.js';
import authRouter from './routes/auth.js';
import transactionsRouter from './routes/transactions.js';

const app = express();

app.use(helmet());
app.use(cors({ origin: true, credentials: true }));
app.use(express.json());
app.use(morgan('dev'));
app.use(
  session({
    secret: config.sessionSecret,
    resave: false,
    saveUninitialized: false,
  })
);

app.get('/health', (_req, res) => {
  res.json({ ok: true });
});

app.use('/api', authRouter);
app.use('/api', transactionsRouter);

app.use((_req, res) => {
  res.status(404).json({ error: 'Not found' });
});

const server = app.listen(config.port, () => {
  // eslint-disable-next-line no-console
  console.log(`Server running on port ${config.port}`);
});

export default server;

