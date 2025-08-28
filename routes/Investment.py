from fastapi import APIRouter
from pydantic import BaseModel
import requests
import logging

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

class CompanyInput(BaseModel):
    company_name: str

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
            logger.info(f"Response headers: {dict(response.headers)}")
            
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            logger.info(f"Full response data: {data}")

            # Check if the response contains a valid 'bestMatches' list
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
                # Check if there's an error message or rate limit info
                if 'Information' in data:
                    logger.warning(f"API Information message: {data['Information']}")
                if 'Error Message' in data:
                    logger.error(f"API Error Message: {data['Error Message']}")
                    
        except requests.exceptions.Timeout:
            logger.error(f"API key {api_key} failed with timeout. Trying next key...")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"API key {api_key} failed with connection error: {e}. Trying next key...")
        except requests.exceptions.HTTPError as e:
            logger.error(f"API key {api_key} failed with HTTP error: {e}. Trying next key...")
        except Exception as e:
            logger.error(f"API key {api_key} failed with unexpected error: {e}. Trying next key...")
    
    logger.warning("All API keys exhausted, returning empty results")
    return []

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
