# Financial AI App

A comprehensive financial management application that authenticates with supported financial institutions, fetches transaction data, and provides AI-powered analysis and insights.

## Features

- **User Authentication**: Secure registration and login system
- **Financial Institution Integration**: Connect to banks using Plaid API
- **Transaction Management**: View, categorize, and analyze all transactions
- **AI Analysis**: Get personalized financial insights and recommendations
- **Account Management**: Manage multiple financial accounts
- **Data Visualization**: Charts and graphs for spending analysis
- **Real-time Sync**: Automatic synchronization with connected accounts

## Tech Stack

### Backend
- **Node.js** with **Express.js**
- **PostgreSQL** database with **Sequelize** ORM
- **Plaid API** for financial institution integration
- **OpenAI API** for AI analysis
- **JWT** for authentication
- **bcrypt** for password hashing

### Frontend
- **React** with **TypeScript**
- **Material-UI** for components
- **React Router** for navigation
- **Axios** for API calls
- **Recharts** for data visualization

## Setup Instructions

### Prerequisites
- Node.js (v16 or higher)
- PostgreSQL database
- Plaid API credentials
- OpenAI API key

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Copy environment configuration:
   ```bash
   cp .env.example .env
   ```

4. Configure your environment variables in `.env`:
   ```env
   # Database
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=financial_ai_app
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password

   # Plaid API
   PLAID_CLIENT_ID=your_plaid_client_id
   PLAID_SECRET=your_plaid_secret
   PLAID_ENV=sandbox

   # OpenAI
   OPENAI_API_KEY=your_openai_api_key

   # JWT
   JWT_SECRET=your-super-secret-jwt-key
   ```

5. Start the database and run migrations:
   ```bash
   npm run dev
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm start
   ```

## Usage

1. **Register/Login**: Create an account or sign in
2. **Connect Accounts**: Use Plaid Link to connect your bank accounts
3. **View Transactions**: Browse and categorize your transactions
4. **Get Insights**: Use AI analysis to understand your spending patterns
5. **Manage Accounts**: Monitor all connected financial accounts

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get user profile
- `PUT /api/auth/me` - Update user profile

### Accounts
- `GET /api/accounts` - Get user accounts
- `POST /api/accounts/link-token` - Create Plaid Link token
- `POST /api/accounts/exchange-token` - Exchange public token
- `POST /api/accounts/:id/sync` - Sync account data

### Transactions
- `GET /api/transactions` - Get transactions with filters
- `POST /api/transactions/sync` - Sync all transactions
- `POST /api/transactions/:id/analyze` - Analyze transaction with AI
- `PUT /api/transactions/:id` - Update transaction

## Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting
- Input validation
- CORS protection
- Helmet security headers

## Development

### Running Tests
```bash
# Backend tests
cd backend
npm test

# Frontend tests
cd frontend
npm test
```

### Building for Production
```bash
# Backend
cd backend
npm run build

# Frontend
cd frontend
npm run build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please contact the development team or create an issue in the repository.