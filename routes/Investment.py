from fastapi import APIRouter
from pydantic import BaseModel
import requests

router = APIRouter(
    prefix='/investment',
    tags=['investment']
)

STOCK_API_KEY = 'A7XIIEJKEPMGRNBK'
SYMBOL_SEARCH_ENDPOINT = 'https://www.alphavantage.co/query'

class CompanyInput(BaseModel):
    company_name: str

def search_company_symbols(query: str):
    """Search for companies using Alpha Vantage SYMBOL_SEARCH"""
    params = {
        'function': 'SYMBOL_SEARCH',
        'keywords': query,
        'apikey': STOCK_API_KEY
    }
    try:
        response = requests.get(SYMBOL_SEARCH_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()

        matches = data.get('bestMatches', [])
        result = []

        for match in matches:
            result.append({
                'symbol': match.get('1. symbol'),
                'name': match.get('2. name'),
                'region': match.get('4. region')
            })

        return result
    except Exception as e:
        return []

@router.post("/")
def search_company(input: CompanyInput):
    results = search_company_symbols(input.company_name)

    return {
        "search_term": input.company_name,
        "match_found": bool(results),
        "companies": results
    }

