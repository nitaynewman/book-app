from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore
import json
from decimal import Decimal, ROUND_HALF_UP
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time


# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix='/investment',
    tags=['investment']
)

STOCK_API_KEYS = [
    'A7XIIEJKEPMGRNBK',
    'A1284I0UD517HKEO',
    'P9GCEOJR5O46ZUQK',
    'IPPQMVWVGNWMWKWY',
]

SYMBOL_SEARCH_ENDPOINT = 'https://www.alphavantage.co/query'
GLOBAL_QUOTE_ENDPOINT = 'https://www.alphavantage.co/query'

# Initialize Firebase
def initialize_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
        logger.info("Firebase already initialized")
    except ValueError:
        # Firebase not initialized, so initialize it
        firebase_key = {
            "type": "service_account",
            "project_id": "expensetracker-e2fc2",
            "private_key_id": "c9022e7623a866ad7ed7ee86efa2152abc4f57e2",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC8y8vDDvUoHPyT\nmIcdFmxfjwYSe+u3VPVh0+04vsbKT6ujS4PySLjA5ePPLSrlCz6JyLZCj3snO36t\n6mmEhsN2XHhV0zv5+lpQSnwxfLrryX7BnE8jey/1DMjwGM3htPx9djXYiJhvdU+2\n87+JTxcF1FHAqF4xF4REqb1hVi/kOveYDwHvHeCu6biUGnzwtF2+FVZuuM7JrFLH\nSJGiNV750no7i8CR+ICYRXwBONwXXbIEEHyuiEf1m8584QdsF/5hiU5qQlakFnjc\n/CuZLMBUBN2My69E6qb1qfZnpF2po9c8TgUwPHWoJZ4y42ydOO0/x8+PDsTi1/fw\nVvvcRF4dAgMBAAECggEAJO18y8ipcaDn02vGY81ewbstLiDgfHHI9EtaT1rbcbdv\nJEfRRWrtfkeJDV0xkm7mWtdwNOkxJr2Xm+dpn7MnWMeh/vGL/et2zlUfYSObQSLe\noPqUrSU7fmQzimjjnkYDC/w68IFZRZXN04RuPqqCX5DFs9gK4nHN3ItR4E/WGr8K\n2WnYmKB3mGFWwdiuPjtfka4J6YwVK6mSSsWp8JGvn4dm4j/MgRBDQWOlWSYkuxMm\nAVeglgfXtnU+1mRSbs4rQIIg96Pj9v6G75hZ/LBrOsDRzO656FDuZGEgmz2wq03v\nlEsOOHIUcOTJ2mhVlS5hvNLJS+8t0xJQpBqWtpz1oQKBgQDldhmeB0exQRGiJ4aT\nSELaUBn7ap2li7rZJW0oJJTggG2qyXutrDAt9oAqTefeXA+XGlrqeQ/h4aqlbgKN\nYPbJHyBt5veTiwYAOdoUd6H/kGY+upAntAosUtJtTpj3S4XT9wrDtDUTRp+ghGJk\nFXtOEu26gZUr2mX2Ws3uLvgLfQKBgQDSoa10l3plMYD48tekSAb+UESqkqHmPX58\nBuFGNS9+5330iw65yS8e7fsqX0ZPJyysKQyADqsnjve4SRh3HX7rbIzifpya6Lmu\nBYc9lDIozaTZpma1ofHxvYwkKc8db0FJ1m1opagn87rJ5gn3yhlmIni7gSBGAS2d\n+008Fb3fIQKBgH93aaelt6e508fWWSW8AJcx5B0MDuMFihhSeB7So3lLHqC/KFtD\nycfepTfa6zFUxrxTwal68t2x9I/NWtGaybzT87nZkjJ+CilZ+dFg27cSShoSnT3Q\n/827fHWIMeU+KOuk0nAAzXMVylrq75VVcZffX/w5O9qOihGeQ8NKiDQpAoGABt1u\nIdauDo5GfdasYJZYZAGJu2V8EVz/ulsfDIK/QYuZ91Zw7G06M+/dt8vTJtFIC3Rr\nC+FugqOOP1tiiL9VW6b2EIu/3uym4J0dg0xJNjs9nDpoLpNQp2heIO+b6IGvxxBO\nEJMVn/e5psrwmDrmCQYmmTXkL2PqcLO4GLU8swECgYAA6uaO6g2DUDXw7PDpQYkT\nwErqXq2S+XrK3B5MwO7TUagrKOlFC0034TD3bBn8Ii+8tSZDvd+JQUHEfGEp2PDs\nQVJfhNvrSax8oq7r5fBoEpN+wbEwvUbb9Cg1NBX3B/sj5LyiniAgZYp33yAoBWQQ\naSjj+NUBkQtPtbFsa/4M5Q==\n-----END PRIVATE KEY-----\n",
            "client_email": "firebase-adminsdk-fbsvc@expensetracker-e2fc2.iam.gserviceaccount.com",
            "client_id": "101662747878940605309",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40expensetracker-e2fc2.iam.gserviceaccount.com",
            "universe_domain": "googleapis.com"
        }
        
        cred = credentials.Certificate(firebase_key)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase initialized successfully")

# Initialize Firebase when module loads
initialize_firebase()


class CompanyInput(BaseModel):
    company_name: str

class DailyUpdateResponse(BaseModel):
    total_users_processed: int
    successful_updates: int
    failed_updates: int
    processing_time_seconds: float
    errors: List[Dict[str, Any]]

def search_company_symbols(query: str):
    """Search for companies using Alpha Vantage SYMBOL_SEARCH, with fallback key logic"""
    logger.info(f"Starting search for query: {query}")
    
    for i, api_key in enumerate(STOCK_API_KEYS):
        logger.info(f"Trying API key {i+1}/{len(STOCK_API_KEYS)}: {api_key[:8]}...")
        
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': query,
            'apikey': api_key
        }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            logger.info(f"Making request to {SYMBOL_SEARCH_ENDPOINT} with params: {params}")
            response = requests.get(SYMBOL_SEARCH_ENDPOINT, params=params, headers=headers, timeout=10)
            logger.info(f"Response status code: {response.status_code}")
            
            response.raise_for_status()
            data = response.json()


            if 'bestMatches' in data:
                matches = data['bestMatches']
                logger.info(f"Found {len(matches)} matches")
                result = [
                    {
                        'symbol': match.get('1. symbol'),
                        'name': match.get('2. name'),
                        'region': match.get('4. region')
                    }
                    for match in matches
                ]
                logger.info(f"Returning {len(result)} results")
                return result
            else:
                logger.warning(f"API key {api_key} used but no 'bestMatches' found. Response: {data}")
                
        except Exception as e:
            logger.error(f"API key {api_key} failed with error: {e}. Trying next key...")

    
    logger.warning("All API keys exhausted, returning empty results")
    return []

def get_stock_quote(symbol: str) -> Dict[str, Any]:
    """Get current stock quote from Alpha Vantage"""
    logger.info(f"Getting stock quote for symbol: {symbol}")
    
    for i, api_key in enumerate(STOCK_API_KEYS):
        logger.info(f"Trying API key {i+1}/{len(STOCK_API_KEYS)} for quote: {api_key[:8]}...")
        
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': api_key
        }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(GLOBAL_QUOTE_ENDPOINT, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Global Quote' in data and data['Global Quote']:
                quote = data['Global Quote']
                current_price = float(quote.get('05. price', 0))
                previous_close = float(quote.get('08. previous close', 0))
                
                if current_price > 0 and previous_close > 0:
                    change_percent = ((current_price - previous_close) / previous_close) * 100
                    
                    return {
                        'symbol': symbol,
                        'current_price': current_price,
                        'previous_close': previous_close,
                        'change_percent': round(change_percent, 2),
                        'change_amount': round(current_price - previous_close, 2)
                    }
                    
            logger.warning(f"API key {api_key} returned invalid data for {symbol}: {data}")
            
        except Exception as e:
            logger.error(f"API key {api_key} failed for quote {symbol}: {e}")
            
        # Rate limiting - wait 12 seconds between requests (5 requests per minute limit)
        time.sleep(12)
    
    logger.error(f"All API keys exhausted for symbol {symbol}")
    return None

def find_stock_symbol_for_investment(investment_name: str) -> str:
    """Find the stock symbol for an investment name"""
    # First try direct search
    matches = search_company_symbols(investment_name)
    
    if matches:
        # Return the first match's symbol
        return matches[0]['symbol']
    
    # If no matches, try some common mappings or variations
    common_mappings = {
        'Tesla Inc': 'TSLA',
        'Apple Inc': 'AAPL',
        'Microsoft Corporation': 'MSFT',
        'Amazon.com Inc': 'AMZN',
        'SPDR S&P 500 ETF Trust': 'SPY',
        'Google': 'GOOGL',
        'Meta': 'META',
        'Netflix': 'NFLX'
    }
    
    return common_mappings.get(investment_name, None)

def calculate_investment_totals_for_user(uid: str) -> List[Dict[str, Any]]:
    """Calculate total amounts for each investment for a specific user"""
    logger.info(f"Calculating investment totals for user: {uid}")
    
    try:
        db = firestore.client()
        
        # Get all investments for this user
        investments_ref = db.collection('investments').where('uid', '==', uid)
        investments = investments_ref.stream()
        
        investment_totals = {}
        
        for investment in investments:
            data = investment.to_dict()
            investment_name = data.get('investmant', '')  # Note: keeping original typo from your schema
            amount = data.get('amount', 0)
            transaction_type = data.get('type', '')
            
            if investment_name not in investment_totals:
                investment_totals[investment_name] = 0
            
            # Add or subtract based on type
            if transaction_type == 'income':
                investment_totals[investment_name] += amount
            elif transaction_type == 'expense':
                investment_totals[investment_name] -= amount
        
        # Convert to list format
        result = []
        for investment_name, total in investment_totals.items():
            if total != 0:  # Only include investments with non-zero totals
                result.append({
                    'investment': investment_name,
                    'total': total
                })
        
        logger.info(f"Found {len(result)} investments with totals for user {uid}")
        return result
        
    except Exception as e:
        logger.error(f"Error calculating investment totals for user {uid}: {e}")
        return []

def update_wallet_amounts(uid: str, wallet_id: str, amount_change: float, transaction_type: str):
    """Update wallet amounts and totals"""
    try:
        db = firestore.client()
        wallet_ref = db.collection('wallets').document(wallet_id)
        wallet_doc = wallet_ref.get()
        
        if not wallet_doc.exists:
            logger.error(f"Wallet {wallet_id} not found for user {uid}")
            return False
            
        wallet_data = wallet_doc.to_dict()
        current_amount = wallet_data.get('amount', 0)
        total_expenses = wallet_data.get('totalExpenses', 0)
        total_income = wallet_data.get('totalIncome', 0)
        
        # Update amounts
        new_amount = current_amount + amount_change if transaction_type == 'income' else current_amount - amount_change
        
        if transaction_type == 'income':
            new_total_income = total_income + abs(amount_change)
            new_total_expenses = total_expenses
        else:
            new_total_expenses = total_expenses + abs(amount_change)
            new_total_income = total_income
        
        # Update wallet
        wallet_ref.update({
            'amount': new_amount,
            'totalIncome': new_total_income,
            'totalExpenses': new_total_expenses,
            'updated': datetime.now()
        })
        
        logger.info(f"Updated wallet {wallet_id} for user {uid}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating wallet {wallet_id} for user {uid}: {e}")
        return False

def create_investment_transaction(uid: str, wallet_id: str, investment_name: str, 
                                amount: float, transaction_type: str, description: str):
    """Create a new investment transaction in Firebase"""
    try:
        db = firestore.client()
        
        investment_data = {
            'uid': uid,
            'walletId': wallet_id,
            'investmant': investment_name,  # Note: keeping original typo from schema
            'amount': abs(amount),  # Always store positive amount
            'type': transaction_type,
            'description': description,
            'date': datetime.now(),
            'image': None,
            'id': None  # Firestore will auto-generate
        }
        
        # Add to investments collection
        doc_ref = db.collection('investments').add(investment_data)
        
        # Update the document with its own ID
        doc_ref[1].update({'id': doc_ref[1].id})
        
        logger.info(f"Created investment transaction for {investment_name}, user {uid}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating investment transaction: {e}")
        return False

def process_user_investments(uid: str) -> Dict[str, Any]:
    """Process all investments for a single user"""
    logger.info(f"Processing investments for user: {uid}")
    
    try:
        # Get investment totals
        investment_totals = calculate_investment_totals_for_user(uid)
        
        if not investment_totals:
            return {
                'uid': uid,
                'status': 'success',
                'message': 'No investments found',
                'processed_investments': 0
            }
        
        processed_count = 0
        errors = []
        
        # Get user's wallets to find a default wallet
        db = firestore.client()
        wallets_ref = db.collection('wallets').where('uid', '==', uid).limit(1)
        wallets = list(wallets_ref.stream())
        
        if not wallets:
            return {
                'uid': uid,
                'status': 'error',
                'message': 'No wallet found for user',
                'processed_investments': 0
            }
        
        default_wallet_id = wallets[0].id
        
        for investment in investment_totals:
            investment_name = investment['investment']
            current_total = investment['total']
            
            try:
                # Find stock symbol
                symbol = find_stock_symbol_for_investment(investment_name)
                
                if not symbol:
                    logger.warning(f"Could not find symbol for investment: {investment_name}")
                    errors.append(f"Symbol not found for {investment_name}")
                    continue
                
                # Get stock quote
                quote = get_stock_quote(symbol)
                
                if not quote:
                    logger.warning(f"Could not get quote for symbol: {symbol}")
                    errors.append(f"Quote not available for {symbol}")
                    continue
                
                # Calculate the change in investment value
                change_percent = quote['change_percent']
                change_amount = (current_total * change_percent) / 100
                
                # Determine transaction type
                transaction_type = 'income' if change_amount >= 0 else 'expense'
                
                description = f"Daily update: {change_percent:+.2f}% change ({symbol})"
                
                # Create investment transaction
                if create_investment_transaction(
                    uid, default_wallet_id, investment_name, 
                    abs(change_amount), transaction_type, description
                ):
                    # Update wallet
                    if update_wallet_amounts(uid, default_wallet_id, abs(change_amount), transaction_type):
                        processed_count += 1
                        logger.info(f"Successfully processed {investment_name} for user {uid}")
                    else:
                        errors.append(f"Failed to update wallet for {investment_name}")
                else:
                    errors.append(f"Failed to create transaction for {investment_name}")
                    
            except Exception as e:
                error_msg = f"Error processing {investment_name}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        return {
            'uid': uid,
            'status': 'success' if processed_count > 0 else 'partial',
            'processed_investments': processed_count,
            'errors': errors
        }
        
    except Exception as e:
        logger.error(f"Error processing investments for user {uid}: {e}")
        return {
            'uid': uid,
            'status': 'error',
            'message': str(e),
            'processed_investments': 0
        }


@router.get("/test-connectivity")
def test_connectivity():
    """Test if we can reach external APIs"""
    try:
        # Test basic connectivity
        response = requests.get("https://httpbin.org/ip", timeout=5)
        external_ip = response.json()
        
        # Test Alpha Vantage connectivity
        test_response = requests.get(SYMBOL_SEARCH_ENDPOINT, timeout=10)
        
        return {
            "external_ip": external_ip,
            "alphavantage_reachable": test_response.status_code == 200,
            "alphavantage_status": test_response.status_code
        }
    except Exception as e:
        return {
            "error": str(e),
            "external_ip": None,
            "alphavantage_reachable": False
        }

@router.post("/search-company")
def search_company(input: CompanyInput):
    logger.info(f"Received search request for: {input.company_name}")
    results = search_company_symbols(input.company_name)
    
    response_data = {
        "search_term": input.company_name,
        "match_found": bool(results),
        "companies": results
    }
    
    logger.info(f"Returning response: {response_data}")
    return response_data

@router.post("/daily-investment-update")
def daily_investment_update():
    """
    Process daily investment updates for all users.
    
    This endpoint should be called once daily, preferably at market close.
    Recommended time: 6:00 PM EST (after US market close) or 1:00 AM IST.
    
    For Israeli users, running at 1:00 AM IST ensures:
    - US markets have closed (9:30 PM IST)
    - European markets data is available
    - System load is typically lower
    """
    start_time = time.time()
    logger.info("Starting daily investment update process")
    
    try:
        # Initialize Firebase connection
        db = firestore.client()
        
        # Get all users
        users_ref = db.collection('users')
        users = users_ref.stream()
        
        total_users = 0
        successful_updates = 0
        failed_updates = 0
        all_errors = []
        
        for user in users:
            total_users += 1
            user_data = user.to_dict()
            uid = user_data.get('uid')
            
            if not uid:
                logger.warning(f"User document missing uid: {user.id}")
                failed_updates += 1
                continue
            
            logger.info(f"Processing user {total_users}: {uid}")
            
            # Process this user's investments
            result = process_user_investments(uid)
            
            if result['status'] == 'success':
                successful_updates += 1
            else:
                failed_updates += 1
                all_errors.append({
                    'uid': uid,
                    'errors': result.get('errors', [result.get('message', 'Unknown error')])
                })
            
            # Rate limiting - wait between users to avoid hitting API limits
            time.sleep(1)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Daily update completed. Users: {total_users}, "
                   f"Successful: {successful_updates}, Failed: {failed_updates}, "
                   f"Time: {processing_time:.2f}s")
        
        return DailyUpdateResponse(
            total_users_processed=total_users,
            successful_updates=successful_updates,
            failed_updates=failed_updates,
            processing_time_seconds=round(processing_time, 2),
            errors=all_errors
        )
        
    except Exception as e:
        logger.error(f"Critical error in daily update: {e}")
        raise HTTPException(status_code=500, detail=f"Daily update failed: {str(e)}")

@router.get("/user-investment-summary/{uid}")
def get_user_investment_summary(uid: str):
    """Get investment summary for a specific user (for testing/debugging)"""
    try:
        investment_totals = calculate_investment_totals_for_user(uid)
        return {
            "uid": uid,
            "investments": investment_totals,
            "total_investments": len(investment_totals)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

