from fastapi import APIRouter
from .auth import router as auth_router
from .plaid import router as plaid_router
from .accounts import router as accounts_router
from .transactions import router as transactions_router
from .users import router as users_router
from .ai_analysis import router as ai_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(plaid_router, prefix="/plaid", tags=["plaid"])
api_router.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["transactions"])
api_router.include_router(ai_router, prefix="/ai", tags=["ai-analysis"])