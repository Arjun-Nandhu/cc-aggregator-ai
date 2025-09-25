import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class PlaidService:
    def __init__(self):
        # Configure Plaid client
        configuration = Configuration(
            host=self._get_plaid_host(),
            api_key={
                'clientId': settings.plaid_client_id,
                'secret': settings.plaid_secret,
            }
        )
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

    def _get_plaid_host(self):
        """Get Plaid host based on environment"""
        if settings.plaid_env == "sandbox":
            return plaid.Environment.sandbox
        elif settings.plaid_env == "development":
            return plaid.Environment.development
        else:
            return plaid.Environment.production

    async def create_link_token(self, user_id: int, webhook_url: Optional[str] = None) -> Dict[str, Any]:
        """Create a link token for Plaid Link"""
        try:
            request = LinkTokenCreateRequest(
                products=[Products('transactions'), Products('auth')],
                client_name="Financial Transaction Aggregator",
                country_codes=[CountryCode('US')],
                language='en',
                webhook=webhook_url,
                user=LinkTokenCreateRequestUser(
                    client_user_id=str(user_id)
                )
            )
            
            response = self.client.link_token_create(request)
            return {
                "link_token": response['link_token'],
                "expiration": response['expiration'].isoformat(),
                "request_id": response['request_id']
            }
        except Exception as e:
            logger.error(f"Error creating link token: {str(e)}")
            raise

    async def exchange_public_token(self, public_token: str) -> Dict[str, str]:
        """Exchange public token for access token"""
        try:
            request = ItemPublicTokenExchangeRequest(
                public_token=public_token
            )
            
            response = self.client.item_public_token_exchange(request)
            return {
                "access_token": response['access_token'],
                "item_id": response['item_id']
            }
        except Exception as e:
            logger.error(f"Error exchanging public token: {str(e)}")
            raise

    async def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get accounts for an access token"""
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            
            accounts = []
            for account in response['accounts']:
                accounts.append({
                    "account_id": account['account_id'],
                    "name": account['name'],
                    "official_name": account.get('official_name'),
                    "type": account['type'],
                    "subtype": account['subtype'],
                    "mask": account.get('mask'),
                    "balances": {
                        "available": account['balances'].get('available'),
                        "current": account['balances'].get('current'),
                        "limit": account['balances'].get('limit'),
                        "iso_currency_code": account['balances'].get('iso_currency_code'),
                        "unofficial_currency_code": account['balances'].get('unofficial_currency_code')
                    },
                    "verification_status": account.get('verification_status'),
                    "persistent_account_id": account.get('persistent_account_id')
                })
            
            return accounts, response['item']
        except Exception as e:
            logger.error(f"Error getting accounts: {str(e)}")
            raise

    async def get_transactions(
        self, 
        access_token: str, 
        start_date: datetime, 
        end_date: datetime,
        account_ids: Optional[List[str]] = None,
        count: int = 500,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get transactions for an access token"""
        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date.date(),
                end_date=end_date.date(),
                account_ids=account_ids,
                count=count,
                offset=offset
            )
            
            response = self.client.transactions_get(request)
            
            transactions = []
            for transaction in response['transactions']:
                transactions.append({
                    "transaction_id": transaction['transaction_id'],
                    "account_id": transaction['account_id'],
                    "amount": transaction['amount'],
                    "iso_currency_code": transaction.get('iso_currency_code'),
                    "unofficial_currency_code": transaction.get('unofficial_currency_code'),
                    "category": transaction.get('category', []),
                    "category_id": transaction.get('category_id'),
                    "merchant_name": transaction.get('merchant_name'),
                    "name": transaction['name'],
                    "original_description": transaction.get('original_description'),
                    "date": transaction['date'].isoformat(),
                    "authorized_date": transaction.get('authorized_date').isoformat() if transaction.get('authorized_date') else None,
                    "authorized_datetime": transaction.get('authorized_datetime').isoformat() if transaction.get('authorized_datetime') else None,
                    "datetime": transaction.get('datetime').isoformat() if transaction.get('datetime') else None,
                    "pending": transaction.get('pending', False),
                    "pending_transaction_id": transaction.get('pending_transaction_id'),
                    "account_owner": transaction.get('account_owner'),
                    "transaction_type": transaction.get('transaction_type'),
                    "transaction_code": transaction.get('transaction_code'),
                    "location": transaction.get('location', {}),
                    "payment_meta": transaction.get('payment_meta', {}),
                    "personal_finance_category": transaction.get('personal_finance_category', {})
                })
            
            return transactions, response['total_transactions']
        except Exception as e:
            logger.error(f"Error getting transactions: {str(e)}")
            raise

    async def sync_transactions(self, access_token: str, cursor: Optional[str] = None) -> Dict[str, Any]:
        """Sync transactions using cursor-based pagination"""
        try:
            request = TransactionsSyncRequest(
                access_token=access_token,
                cursor=cursor
            )
            
            response = self.client.transactions_sync(request)
            
            # Process added transactions
            added_transactions = []
            for transaction in response['added']:
                added_transactions.append({
                    "transaction_id": transaction['transaction_id'],
                    "account_id": transaction['account_id'],
                    "amount": transaction['amount'],
                    "iso_currency_code": transaction.get('iso_currency_code'),
                    "unofficial_currency_code": transaction.get('unofficial_currency_code'),
                    "category": transaction.get('category', []),
                    "category_id": transaction.get('category_id'),
                    "merchant_name": transaction.get('merchant_name'),
                    "name": transaction['name'],
                    "original_description": transaction.get('original_description'),
                    "date": transaction['date'].isoformat(),
                    "authorized_date": transaction.get('authorized_date').isoformat() if transaction.get('authorized_date') else None,
                    "authorized_datetime": transaction.get('authorized_datetime').isoformat() if transaction.get('authorized_datetime') else None,
                    "datetime": transaction.get('datetime').isoformat() if transaction.get('datetime') else None,
                    "pending": transaction.get('pending', False),
                    "pending_transaction_id": transaction.get('pending_transaction_id'),
                    "account_owner": transaction.get('account_owner'),
                    "transaction_type": transaction.get('transaction_type'),
                    "transaction_code": transaction.get('transaction_code'),
                    "location": transaction.get('location', {}),
                    "payment_meta": transaction.get('payment_meta', {}),
                    "personal_finance_category": transaction.get('personal_finance_category', {})
                })
            
            # Process modified transactions
            modified_transactions = []
            for transaction in response['modified']:
                modified_transactions.append({
                    "transaction_id": transaction['transaction_id'],
                    "account_id": transaction['account_id'],
                    "amount": transaction['amount'],
                    # ... same fields as added transactions
                })
            
            # Process removed transaction IDs
            removed_transaction_ids = [t['transaction_id'] for t in response['removed']]
            
            return {
                "added": added_transactions,
                "modified": modified_transactions,
                "removed": removed_transaction_ids,
                "next_cursor": response['next_cursor'],
                "has_more": response['has_more']
            }
        except Exception as e:
            logger.error(f"Error syncing transactions: {str(e)}")
            raise

    async def get_institution(self, institution_id: str) -> Dict[str, Any]:
        """Get institution details by ID"""
        try:
            request = InstitutionsGetByIdRequest(
                institution_id=institution_id,
                country_codes=[CountryCode('US')]
            )
            
            response = self.client.institutions_get_by_id(request)
            institution = response['institution']
            
            return {
                "institution_id": institution['institution_id'],
                "name": institution['name'],
                "country": institution.get('country'),
                "url": institution.get('url'),
                "primary_color": institution.get('primary_color'),
                "logo": institution.get('logo')
            }
        except Exception as e:
            logger.error(f"Error getting institution: {str(e)}")
            raise