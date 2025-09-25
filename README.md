# Financial Data Aggregator

A comprehensive financial data aggregation application that authenticates with financial institutions, fetches transactions, and provides AI-powered analysis of financial data.

## Features

- **Bank Account Integration**: Connect to multiple financial institutions via Plaid API
- **Transaction Management**: Fetch and store transaction data with categorization
- **AI-Powered Analysis**: 
  - Spending pattern analysis
  - Anomaly detection
  - Budget insights
  - Financial trend analysis
- **Secure Authentication**: JWT-based user authentication
- **RESTful API**: Complete API for data access and analysis
- **Database Storage**: PostgreSQL/SQLite support for data persistence

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Database      │
│   (React/Vue)   │◄──►│   Backend       │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Plaid API     │
                       │   (Bank Data)   │
                       └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (optional, SQLite used by default)
- Plaid account and API credentials

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository>
   cd financial-app
   pip install -r requirements.txt
   ```

2. **Environment Configuration**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Database Setup**:
   ```bash
   # Initialize database
   alembic upgrade head
   ```

4. **Run the Application**:
   ```bash
   uvicorn app.main:app --reload
   ```

### Docker Setup

```bash
# Using Docker Compose
docker-compose up -d

# Or build and run manually
docker build -t financial-app .
docker run -p 8000:8000 financial-app
```

## API Endpoints

### Authentication
- `POST /register` - Register new user
- `POST /token` - Login and get access token
- `GET /users/me` - Get current user info

### Plaid Integration
- `POST /plaid/link-token` - Create Plaid link token
- `POST /plaid/exchange-token` - Exchange public token for access token

### Data Access
- `GET /accounts` - Get user accounts
- `GET /transactions` - Get user transactions
- `GET /analysis/history` - Get analysis history

### AI Analysis
- `POST /analysis/spending-patterns` - Analyze spending patterns
- `POST /analysis/anomalies` - Detect spending anomalies

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/financial_app

# Security
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Plaid Configuration
PLAID_CLIENT_ID=your-plaid-client-id
PLAID_SECRET=your-plaid-secret
PLAID_ENV=sandbox  # sandbox, development, production
PLAID_PRODUCTS=transactions,accounts,identity
```

### Plaid Setup

1. Create a Plaid account at [plaid.com](https://plaid.com)
2. Get your API credentials from the Plaid Dashboard
3. Set up your environment variables
4. For development, use the `sandbox` environment

## Usage Examples

### 1. Register and Login

```bash
# Register
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Login
curl -X POST "http://localhost:8000/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password123"
```

### 2. Connect Bank Account

```bash
# Get link token
curl -X POST "http://localhost:8000/plaid/link-token" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Exchange public token (after Plaid Link flow)
curl -X POST "http://localhost:8000/plaid/exchange-token" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"public_token": "public-sandbox-xxx", "institution_id": "ins_1"}'
```

### 3. Analyze Spending

```bash
# Get spending patterns
curl -X POST "http://localhost:8000/analysis/spending-patterns?days=90" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"

# Detect anomalies
curl -X POST "http://localhost:8000/analysis/anomalies?days=30" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Data Models

### User
- User authentication and profile information

### Institution
- Financial institution details (banks, credit unions, etc.)

### Account
- Bank accounts linked to users
- Account metadata and status

### Transaction
- Individual transactions with categorization
- Merchant information and spending patterns

### AIAnalysis
- Results of AI-powered financial analysis
- Confidence scores and analysis metadata

## Security Features

- **Password Hashing**: bcrypt for secure password storage
- **JWT Authentication**: Secure token-based authentication
- **Data Encryption**: Sensitive data encrypted at rest
- **API Security**: Rate limiting and input validation
- **Plaid Security**: Bank-level security through Plaid

## AI Analysis Features

### Spending Pattern Analysis
- Category-wise spending breakdown
- Monthly and daily spending trends
- Top merchants and spending locations
- Average daily spending calculations

### Anomaly Detection
- Statistical outlier detection
- Large transaction identification
- Unusual spending pattern alerts
- Confidence scoring for anomalies

### Future Enhancements
- Budget recommendations
- Investment analysis
- Credit score insights
- Financial goal tracking

## Development

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Testing

```bash
# Run tests (when implemented)
pytest

# Run with coverage
pytest --cov=app
```

## Production Deployment

### Environment Setup
1. Use PostgreSQL for production database
2. Set strong SECRET_KEY
3. Use production Plaid environment
4. Enable HTTPS
5. Set up monitoring and logging

### Security Checklist
- [ ] Strong secret keys
- [ ] HTTPS enabled
- [ ] Database encryption
- [ ] API rate limiting
- [ ] Input validation
- [ ] Error handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue in the repository
- Check the documentation
- Review the API endpoints

## Roadmap

- [ ] Frontend dashboard
- [ ] Mobile app
- [ ] Advanced AI models
- [ ] Real-time notifications
- [ ] Multi-currency support
- [ ] Investment tracking
- [ ] Bill reminders
- [ ] Financial goal setting