#!/usr/bin/env python3
"""
API testing script for Financial Data Aggregator
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test API health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ API is running")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        return False

def test_user_registration():
    """Test user registration"""
    try:
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code == 200:
            print("✅ User registration successful")
            return response.json()
        else:
            print(f"❌ User registration failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ User registration failed: {e}")
        return None

def test_user_login():
    """Test user login"""
    try:
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        if response.status_code == 200:
            print("✅ User login successful")
            return response.json()["access_token"]
        else:
            print(f"❌ User login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ User login failed: {e}")
        return None

def test_protected_endpoint(token):
    """Test protected endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/accounts", headers=headers)
        if response.status_code == 200:
            print("✅ Protected endpoint access successful")
            return True
        else:
            print(f"❌ Protected endpoint access failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Protected endpoint access failed: {e}")
        return False

def test_plaid_link_token(token):
    """Test Plaid link token creation"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(f"{BASE_URL}/plaid/link-token", headers=headers)
        if response.status_code == 200:
            print("✅ Plaid link token creation successful")
            return True
        else:
            print(f"❌ Plaid link token creation failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Plaid link token creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing Financial Data Aggregator API...")
    print("=" * 50)
    
    # Test API health
    if not test_health():
        print("❌ API is not running. Please start the server first.")
        return
    
    print()
    
    # Test user registration
    user = test_user_registration()
    if not user:
        print("❌ User registration failed. Tests cannot continue.")
        return
    
    print()
    
    # Test user login
    token = test_user_login()
    if not token:
        print("❌ User login failed. Tests cannot continue.")
        return
    
    print()
    
    # Test protected endpoint
    test_protected_endpoint(token)
    
    print()
    
    # Test Plaid integration (requires Plaid credentials)
    test_plaid_link_token(token)
    
    print()
    print("=" * 50)
    print("🎉 API testing completed!")

if __name__ == "__main__":
    main()