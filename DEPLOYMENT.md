# Deployment Guide

This guide covers deployment options for the Financial Transaction Aggregator application.

## Prerequisites

- Docker and Docker Compose
- Plaid API credentials (production environment)
- PostgreSQL database
- Redis instance
- SSL certificate (for production)

## Environment Configuration

### 1. Production Environment Variables

Create a `.env.prod` file with production settings:

```env
# Database (use managed PostgreSQL service)
DATABASE_URL=postgresql://user:password@prod-db-host:5432/fintech_app

# Plaid API (Production)
PLAID_CLIENT_ID=your_production_client_id
PLAID_SECRET=your_production_secret
PLAID_ENV=production

# Security (generate strong keys)
SECRET_KEY=your-super-secure-production-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Redis (use managed Redis service)
REDIS_URL=redis://prod-redis-host:6379/0

# AI Analysis
OPENAI_API_KEY=your_production_openai_key

# Application
DEBUG=false
```

### 2. SSL Configuration

Ensure your deployment has proper SSL/TLS configuration:
- Use Let's Encrypt or commercial SSL certificates
- Configure HTTPS redirect
- Set secure cookie flags

## Deployment Options

### Option 1: Docker Compose (Recommended for small deployments)

1. **Production Docker Compose**

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "80:8000"
      - "443:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - PLAID_CLIENT_ID=${PLAID_CLIENT_ID}
      - PLAID_SECRET=${PLAID_SECRET}
      - PLAID_ENV=production
      - SECRET_KEY=${SECRET_KEY}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./ssl:/app/ssl
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  celery:
    build: .
    command: celery -A app.tasks worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  celery-beat:
    build: .
    command: celery -A app.tasks beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: fintech_app
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl/certs
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
```

2. **Deploy**

```bash
# Load environment variables
export $(cat .env.prod | xargs)

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec app alembic upgrade head
```

### Option 2: Kubernetes

1. **Create Kubernetes manifests**

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: fintech-app

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
  namespace: fintech-app
data:
  PLAID_ENV: "production"
  ALGORITHM: "HS256"
  ACCESS_TOKEN_EXPIRE_MINUTES: "30"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: fintech-app
type: Opaque
stringData:
  DATABASE_URL: "postgresql://user:password@postgres:5432/fintech_app"
  PLAID_CLIENT_ID: "your_plaid_client_id"
  PLAID_SECRET: "your_plaid_secret"
  SECRET_KEY: "your_secret_key"
  REDIS_URL: "redis://redis:6379/0"
  OPENAI_API_KEY: "your_openai_key"

---
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fintech-app
  namespace: fintech-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: fintech-app
  template:
    metadata:
      labels:
        app: fintech-app
    spec:
      containers:
      - name: app
        image: fintech-app:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: app-config
        - secretRef:
            name: app-secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5

---
# k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: fintech-app-service
  namespace: fintech-app
spec:
  selector:
    app: fintech-app
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

2. **Deploy to Kubernetes**

```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment
kubectl get pods -n fintech-app
kubectl get services -n fintech-app
```

### Option 3: Cloud Platforms

#### AWS Deployment

1. **Using AWS ECS with Fargate**

```json
{
  "family": "fintech-app",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "fintech-app",
      "image": "your-ecr-repo/fintech-app:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "PLAID_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:database-url"
        },
        {
          "name": "PLAID_CLIENT_ID",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:plaid-client-id"
        }
      ]
    }
  ]
}
```

2. **Services to use:**
   - **ECS Fargate**: Container orchestration
   - **RDS PostgreSQL**: Managed database
   - **ElastiCache Redis**: Managed Redis
   - **Application Load Balancer**: Load balancing
   - **Route 53**: DNS management
   - **Certificate Manager**: SSL certificates
   - **Secrets Manager**: Secret management

#### Google Cloud Platform

1. **Using Cloud Run**

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: fintech-app
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cloudsql-instances: project:region:instance
    spec:
      containers:
      - image: gcr.io/project/fintech-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
```

2. **Services to use:**
   - **Cloud Run**: Serverless containers
   - **Cloud SQL PostgreSQL**: Managed database
   - **Memorystore Redis**: Managed Redis
   - **Cloud Load Balancing**: Load balancing
   - **Cloud DNS**: DNS management
   - **Secret Manager**: Secret management

## Database Migration in Production

1. **Backup database before migration**

```bash
# PostgreSQL backup
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql
```

2. **Run migrations**

```bash
# Docker
docker-compose exec app alembic upgrade head

# Kubernetes
kubectl exec -it deployment/fintech-app -n fintech-app -- alembic upgrade head
```

3. **Rollback if needed**

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade revision_id
```

## Monitoring and Logging

### 1. Application Monitoring

- **Health checks**: `/health` endpoint
- **Metrics**: Prometheus metrics
- **APM**: New Relic, DataDog, or similar
- **Uptime monitoring**: External monitoring service

### 2. Logging

```python
# Configure structured logging
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
        }
        return json.dumps(log_obj)

# Use in production
logging.basicConfig(level=logging.INFO, handlers=[
    logging.StreamHandler()
])
```

### 3. Error Tracking

- **Sentry**: Error tracking and performance monitoring
- **Rollbar**: Real-time error tracking
- **Bugsnag**: Error monitoring

## Security Considerations

### 1. Environment Security

- Use secrets management services
- Rotate secrets regularly
- Enable audit logging
- Implement proper IAM roles

### 2. Application Security

- Enable HTTPS everywhere
- Implement rate limiting
- Use WAF (Web Application Firewall)
- Regular security scans

### 3. Database Security

- Enable encryption at rest
- Use connection encryption
- Implement proper backup encryption
- Regular security updates

## Performance Optimization

### 1. Database Optimization

- Implement proper indexing
- Use connection pooling
- Monitor query performance
- Implement read replicas

### 2. Caching Strategy

- Redis for session storage
- Application-level caching
- CDN for static assets
- Database query caching

### 3. Scaling

- Horizontal scaling with load balancers
- Auto-scaling based on metrics
- Database sharding if needed
- Background task optimization

## Backup and Disaster Recovery

### 1. Database Backups

```bash
# Automated daily backups
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump $DATABASE_URL | gzip > backup_$DATE.sql.gz

# Upload to cloud storage
aws s3 cp backup_$DATE.sql.gz s3://your-backup-bucket/
```

### 2. Application Backups

- Container image backups
- Configuration backups
- SSL certificate backups
- Log backups

### 3. Disaster Recovery Plan

- Document recovery procedures
- Test recovery processes regularly
- Implement multi-region deployments
- Monitor backup integrity

## Compliance and Regulations

### 1. Financial Data Compliance

- PCI DSS compliance for payment data
- SOC 2 Type II certification
- GDPR compliance for EU users
- Regular security audits

### 2. Data Retention

- Implement data retention policies
- Secure data deletion procedures
- Audit trail maintenance
- User data export capabilities

## Troubleshooting

### 1. Common Issues

- Database connection failures
- Plaid API rate limits
- Memory leaks in long-running processes
- SSL certificate expiration

### 2. Debugging Tools

```bash
# Check application logs
docker-compose logs app

# Check database connectivity
docker-compose exec app python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"

# Check Redis connectivity
docker-compose exec app python -c "import redis; r=redis.from_url('redis://redis:6379/0'); print(r.ping())"
```

### 3. Performance Debugging

- Monitor response times
- Check database query performance
- Analyze memory usage
- Monitor background task queues

This deployment guide provides a comprehensive approach to deploying the Financial Transaction Aggregator in production environments with proper security, monitoring, and scalability considerations.