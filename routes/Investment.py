from fastapi import APIRouter
from pydantic import BaseModel
import requests

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
    for api_key in STOCK_API_KEYS:
        params = {
            'function': 'SYMBOL_SEARCH',
            'keywords': query,
            'apikey': api_key
        }
        try:
            response = requests.get(SYMBOL_SEARCH_ENDPOINT, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check if the response contains a valid 'bestMatches' list
            if 'bestMatches' in data:
                matches = data['bestMatches']
                result = [
                    {
                        'symbol': match.get('1. symbol'),
                        'name': match.get('2. name'),
                        'region': match.get('4. region')
                    }
                    for match in matches
                ]
                return result
            else:
                print(f"API key {api_key} used but no 'bestMatches' found. Trying next key...")
        except Exception as e:
            print(f"API key {api_key} failed with error: {e}. Trying next key...")
    return []

@router.post("/search-company")
def search_company(input: CompanyInput):
    results = search_company_symbols(input.company_name)

    return {
        "search_term": input.company_name,
        "match_found": bool(results),
        "companies": results
    }
