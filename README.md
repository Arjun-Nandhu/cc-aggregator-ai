# Financial Transaction Aggregator

A comprehensive financial transaction aggregation and analysis platform that authenticates with financial institutions, fetches transactions, and stores data for AI-powered analysis.

## Features

### Core Functionality
- **Bank Authentication**: Secure authentication with 11,000+ financial institutions via Plaid API
- **Transaction Aggregation**: Automatic fetching and synchronization of transactions
- **Account Management**: Multi-account support across checking, savings, credit cards, and investments
- **Real-time Sync**: Background synchronization with cursor-based pagination for efficiency
- **Data Storage**: PostgreSQL database optimized for financial data with proper indexing

### AI-Powered Analysis
- **Smart Categorization**: Automatic transaction categorization using AI/ML
- **Sentiment Analysis**: Understand spending patterns and emotions
- **Spending Insights**: Detailed analytics on spending habits and trends
- **Custom Tags**: AI-generated tags for better transaction organization

### API & Integration
- **RESTful API**: Comprehensive API with authentication and rate limiting
- **Real-time Updates**: WebSocket support for live transaction updates
- **Background Tasks**: Celery-based background processing for heavy operations
- **Webhook Support**: Plaid webhook integration for instant updates

### Security & Compliance
- **JWT Authentication**: Secure user authentication with token-based access
- **Data Encryption**: Sensitive data encryption at rest and in transit
- **GDPR Compliant**: Data privacy and user control features
- **Rate Limiting**: API rate limiting and abuse prevention

## Technology Stack

### Backend
- **FastAPI**: Modern, fast web framework for building APIs
- **SQLAlchemy**: SQL toolkit and ORM for database operations
- **PostgreSQL**: Primary database for transaction and user data
- **Redis**: Caching and background task queue
- **Celery**: Distributed task queue for background processing

### Financial Data
- **Plaid API**: Financial institution authentication and data aggregation
- **Open Banking**: Support for open banking standards
- **Real-time Sync**: Cursor-based transaction synchronization

### AI/ML
- **OpenAI GPT**: Transaction analysis and categorization
- **scikit-learn**: Machine learning for spending pattern analysis
- **pandas/numpy**: Data processing and analytics

### Infrastructure
- **Docker**: Containerized deployment
- **Docker Compose**: Multi-service orchestration
- **Alembic**: Database migration management

## Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Plaid API credentials (sign up at [Plaid](https://plaid.com))

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd financial-transaction-aggregator
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start services with Docker**
   ```bash
   docker-compose up postgres redis -d
   ```

6. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

7. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

8. **Start background worker (in another terminal)**
   ```bash
   celery -A app.tasks worker --loglevel=info
   ```

### Using the Setup Script
Alternatively, use the automated setup script:
```bash
python scripts/setup.py
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/fintech_app

# Plaid API (Get from https://plaid.com)
PLAID_CLIENT_ID=your_plaid_client_id
PLAID_SECRET=your_plaid_secret
PLAID_ENV=sandbox  # sandbox, development, or production

# Application Security
SECRET_KEY=your-super-secret-jwt-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis
REDIS_URL=redis://localhost:6379/0

# AI Analysis (Optional)
OPENAI_API_KEY=your_openai_api_key_here
```

### Plaid Environment Setup

1. **Sandbox**: For development and testing
   - Use test credentials provided by Plaid
   - No real money or accounts involved
   
2. **Development**: For testing with real but limited data
   - Requires Plaid approval
   - Limited to your own accounts
   
3. **Production**: For live application
   - Requires Plaid approval and compliance review
   - Full access to all supported institutions

## API Documentation

Once the application is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login

#### Plaid Integration
- `POST /api/v1/plaid/link-token` - Create Plaid Link token
- `POST /api/v1/plaid/exchange-token` - Exchange public token for access token
- `POST /api/v1/plaid/sync-transactions/{item_id}` - Manual transaction sync

#### Accounts
- `GET /api/v1/accounts/` - Get user accounts
- `GET /api/v1/accounts/summary/overview` - Get account summary

#### Transactions
- `GET /api/v1/transactions/` - Get transactions with filtering
- `GET /api/v1/transactions/analytics` - Get spending analytics
- `PUT /api/v1/transactions/{id}` - Update transaction (AI tags, etc.)

## Usage Examples

### 1. User Registration and Authentication

```python
import requests

# Register user
response = requests.post("http://localhost:8000/api/v1/auth/register", json={
    "email": "user@example.com",
    "password": "securepassword",
    "first_name": "John",
    "last_name": "Doe"
})

# Login
response = requests.post("http://localhost:8000/api/v1/auth/login", data={
    "username": "user@example.com",
    "password": "securepassword"
})
token = response.json()["access_token"]
```

### 2. Connect Bank Account

```python
headers = {"Authorization": f"Bearer {token}"}

# Create link token
response = requests.post("http://localhost:8000/api/v1/plaid/link-token", 
                        json={"user_id": 1}, headers=headers)
link_token = response.json()["link_token"]

# Use link_token in Plaid Link frontend
# After user completes Link flow, exchange public token
response = requests.post("http://localhost:8000/api/v1/plaid/exchange-token",
                        json={"public_token": "public-sandbox-xxx"}, 
                        headers=headers)
```

### 3. Fetch Transactions

```python
# Get recent transactions
response = requests.get("http://localhost:8000/api/v1/transactions/", 
                       headers=headers)
transactions = response.json()

# Get analytics
response = requests.get("http://localhost:8000/api/v1/transactions/analytics?period=30d", 
                       headers=headers)
analytics = response.json()
```

## Architecture

### Database Schema

The application uses a normalized database schema with the following key tables:

- **users**: User accounts and authentication
- **institutions**: Financial institution metadata
- **plaid_items**: Plaid connection items per user
- **accounts**: Bank accounts (checking, savings, credit, etc.)
- **transactions**: Individual transaction records with AI analysis fields

### Background Processing

The application uses Celery for background tasks:

- **Transaction Sync**: Periodic synchronization with financial institutions
- **AI Analysis**: Background processing for transaction categorization
- **Webhook Processing**: Handle real-time updates from Plaid

### Security Considerations

- All sensitive data encrypted in transit and at rest
- JWT tokens with configurable expiration
- Rate limiting on API endpoints
- Input validation and sanitization
- SQL injection prevention through ORM

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Deployment

### Docker Deployment

```bash
# Build and run all services
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Environment-Specific Configuration

- **Development**: Use `sandbox` Plaid environment
- **Staging**: Use `development` Plaid environment
- **Production**: Use `production` Plaid environment with proper SSL

## Monitoring and Logging

The application includes comprehensive logging:

- **Application logs**: Structured logging with timestamps
- **Database queries**: SQL query logging for debugging
- **API access logs**: Request/response logging
- **Background task logs**: Celery task execution logs

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Check the API documentation at `/docs`
- Review the Plaid documentation for integration questions

## Roadmap

- [ ] Frontend React/Vue.js application
- [ ] Mobile app with React Native
- [ ] Advanced AI spending insights
- [ ] Budget planning and alerts
- [ ] Investment tracking
- [ ] Multi-currency support
- [ ] Export to CSV/Excel
- [ ] Financial goal tracking
