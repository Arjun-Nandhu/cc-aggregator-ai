import plaid
from plaid.api import plaid_api
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

from app.config import settings


class PlaidClient:
    def __init__(self):
        configuration = plaid.Configuration(
            host=plaid.Environment[settings.plaid_env],
            api_key={
                'clientId': settings.plaid_client_id,
                'secret': settings.plaid_secret,
            }
        )
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

    def create_link_token(self, user_id: str) -> Dict[str, Any]:
        """Create a link token for Plaid Link"""
        request = LinkTokenCreateRequest(
            products=[Products('transactions')],
            client_name="Financial Data Aggregator",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id=user_id)
        )
        
        response = self.client.link_token_create(request)
        return {
            'link_token': response['link_token'],
            'expiration': response['expiration']
        }

    def exchange_public_token(self, public_token: str) -> Dict[str, Any]:
        """Exchange public token for access token"""
        request = ItemPublicTokenExchangeRequest(public_token=public_token)
        response = self.client.item_public_token_exchange(request)
        return {
            'access_token': response['access_token'],
            'item_id': response['item_id']
        }

    def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """Get all accounts for an access token"""
        request = AccountsGetRequest(access_token=access_token)
        response = self.client.accounts_get(request)
        return response['accounts']

    def get_transactions(self, access_token: str, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Get transactions for an access token"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
            
        request = TransactionsGetRequest(
            access_token=access_token,
            start_date=start_date.date(),
            end_date=end_date.date()
        )
        response = self.client.transactions_get(request)
        return {
            'transactions': response['transactions'],
            'total_transactions': response['total_transactions']
        }

    def get_institution_by_id(self, institution_id: str) -> Dict[str, Any]:
        """Get institution information by ID"""
        request = plaid.model.institutions_get_by_id_request.InstitutionsGetByIdRequest(
            institution_id=institution_id,
            country_codes=[CountryCode('US')]
        )
        response = self.client.institutions_get_by_id(request)
        return response['institution']


# Global Plaid client instance
plaid_client = PlaidClient()