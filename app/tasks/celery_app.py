from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "financial_aggregator",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.transaction_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    "sync-all-transactions": {
        "task": "app.tasks.transaction_tasks.sync_all_transactions_task",
        "schedule": 3600.0,  # Run every hour
    },
    "analyze-recent-transactions": {
        "task": "app.tasks.transaction_tasks.analyze_recent_transactions_task",
        "schedule": 1800.0,  # Run every 30 minutes
    },
}