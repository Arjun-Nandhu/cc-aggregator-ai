import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from datetime import datetime, timedelta
from typing import List, Dict, Any
from app.config import settings

# Configure Plaid client
configuration = plaid.Configuration(
    host=plaid.Environment[settings.plaid_env],
    api_key={
        'clientId': settings.plaid_client_id,
        'secret': settings.plaid_secret,
    }
)

api_client = plaid.ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)


class PlaidService:
    """Service for interacting with Plaid API"""
    
    @staticmethod
    def create_link_token(user_id: str) -> Dict[str, Any]:
        """Create a link token for Plaid Link"""
        request = LinkTokenCreateRequest(
            products=[Products('transactions'), Products('accounts'), Products('identity')],
            client_name=settings.app_name,
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(
                client_user_id=user_id
            )
        )
        
        response = client.link_token_create(request)
        return {
            'link_token': response['link_token'],
            'expiration': response['expiration']
        }
    
    @staticmethod
    def exchange_public_token(public_token: str) -> str:
        """Exchange public token for access token"""
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = client.item_public_token_exchange(request)
        return response['access_token']
    
    @staticmethod
    def get_accounts(access_token: str) -> List[Dict[str, Any]]:
        """Get accounts for an access token"""
        request = AccountsGetRequest(access_token=access_token)
        response = client.accounts_get(request)
        return response['accounts']
    
    @staticmethod
    def get_transactions(access_token: str, start_date: datetime = None, end_date: datetime = None) -> List[Dict[str, Any]]:
        """Get transactions for an access token"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date.date(),
            end_date=end_date.date(),
            options=TransactionsGetRequestOptions(
                count=500,
                offset=0
            )
        )
        
        response = client.transactions_get(request)
        return response['transactions']
    
    @staticmethod
    def get_institution_by_id(institution_id: str) -> Dict[str, Any]:
        """Get institution information by ID"""
        # This would typically use the institutions endpoint
        # For now, return basic info
        return {
            'institution_id': institution_id,
            'name': 'Unknown Institution'
        }