# Financial Data Aggregator

A comprehensive financial data aggregation application that authenticates with financial institutions, fetches transactions, and provides AI-powered analysis of financial data.

## Features

- **Multi-Institution Support**: Connect to multiple financial institutions via Plaid API
- **Secure Authentication**: JWT-based user authentication and OAuth for financial institutions
- **Transaction Aggregation**: Fetch and store transactions from all connected accounts
- **AI-Powered Analysis**: 
  - Spending pattern analysis
  - Budget performance tracking
  - Anomaly detection
  - Financial insights generation
- **RESTful API**: Complete API for frontend integration
- **Database Storage**: PostgreSQL for reliable data persistence
- **Real-time Processing**: Background tasks for data processing

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI App   │    │   PostgreSQL    │
│   (React/Vue)   │◄──►│   (Python)      │◄──►│   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Plaid API     │
                       │   (Financial   │
                       │   Institutions) │
                       └─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis (optional, for background tasks)
- Plaid API credentials

### Installation

1. **Clone and setup**:
```bash
git clone <repository>
cd financial-data-aggregator
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Environment configuration**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. **Database setup**:
```bash
# Start PostgreSQL
# Create database
createdb financial_app

# Run migrations
alembic upgrade head
```

5. **Run the application**:
```bash
uvicorn app.main:app --reload
```

### Docker Setup

```bash
# Start all services
docker-compose up -d

# Run migrations
docker-compose exec app alembic upgrade head
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login

### Plaid Integration
- `POST /plaid/link-token` - Create link token for account connection
- `POST /plaid/exchange-token` - Exchange public token for access token

### Data Retrieval
- `GET /accounts` - Get user's connected accounts
- `GET /transactions` - Get user's transactions

### AI Analysis
- `POST /ai-analysis/spending-patterns` - Analyze spending patterns
- `POST /ai-analysis/budget-performance` - Analyze budget performance
- `POST /ai-analysis/anomaly-detection` - Detect spending anomalies
- `GET /ai-analysis` - Get analysis results

## Configuration

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/financial_app
REDIS_URL=redis://localhost:6379/0

# Plaid Configuration
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=sandbox  # sandbox, development, or production

# Security
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### Plaid Setup

1. Sign up for a Plaid account at [plaid.com](https://plaid.com)
2. Get your `client_id` and `secret` from the Plaid dashboard
3. Configure your environment variables
4. Start with `sandbox` environment for testing

## Database Schema

### Core Tables

- **users**: User accounts and authentication
- **institutions**: Financial institutions (banks, credit unions, etc.)
- **accounts**: User's connected financial accounts
- **transactions**: Individual transactions from all accounts
- **ai_analyses**: AI analysis results and insights

### Key Relationships

- Users have many Accounts
- Accounts belong to Institutions
- Transactions belong to Accounts and Users
- AI Analyses belong to Users

## AI Analysis Features

### Spending Pattern Analysis
- Daily, weekly, monthly spending trends
- Category-based spending breakdown
- Top merchants analysis
- Spending velocity tracking

### Budget Performance
- Category-wise budget tracking
- Over/under budget alerts
- Monthly budget performance metrics
- Budget optimization suggestions

### Anomaly Detection
- Unusual transaction detection
- High-value transaction alerts
- Category-specific anomaly detection
- Spending pattern deviation analysis

## Development

### Project Structure

```
financial-data-aggregator/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── crud.py              # Database operations
│   ├── auth.py              # Authentication logic
│   ├── plaid_client.py      # Plaid API integration
│   └── ai_analysis.py       # AI analysis engine
├── alembic/                 # Database migrations
├── requirements.txt         # Python dependencies
├── docker-compose.yml      # Docker services
├── Dockerfile              # Docker configuration
└── README.md               # This file
```

### Adding New Features

1. **Database Changes**: Create new migration with `alembic revision --autogenerate -m "description"`
2. **API Endpoints**: Add to `app/main.py`
3. **AI Analysis**: Extend `app/ai_analysis.py`
4. **Data Models**: Update `app/models.py` and `app/schemas.py`

### Testing

```bash
# Run tests (when implemented)
pytest

# Test API endpoints
curl -X GET "http://localhost:8000/"
```

## Security Considerations

- All API endpoints require authentication (except registration/login)
- Passwords are hashed using bcrypt
- JWT tokens for session management
- Plaid handles financial institution authentication
- Database connections use environment variables
- CORS configured for frontend integration

## Production Deployment

1. **Environment**: Set `PLAID_ENV=production`
2. **Database**: Use production PostgreSQL instance
3. **Security**: Use strong secret keys and HTTPS
4. **Monitoring**: Add logging and monitoring
5. **Scaling**: Consider Redis for session storage and Celery for background tasks

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions and support, please open an issue in the repository.