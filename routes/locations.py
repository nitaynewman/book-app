from fastapi import APIRouter, HTTPException
import os, json, uuid
from typing import List
from pydantic import BaseModel


router = APIRouter(
  prefix="/locations",
  tags=["locations"]
)

DATA_FILE = "data/cities_data.json"

# Pydantic models
class Position(BaseModel):
    lat: str
    lng: str

class CityCreate(BaseModel):
    cityName: str
    country: str
    emoji: str
    date: str
    notes: str
    position: Position

class City(BaseModel):
    id: str
    cityName: str
    country: str
    emoji: str
    date: str
    notes: str
    position: Position

class CitiesData(BaseModel):
    cities: List[City]

# Helper functions
def read_cities() -> CitiesData:
    """Read cities from JSON file"""
    if not os.path.exists(DATA_FILE):
        # Create initial file if it doesn't exist
        initial_data = {"cities": []}
        with open(DATA_FILE, 'w') as f:
            json.dump(initial_data, f, indent=2)
        return CitiesData(**initial_data)
    
    with open(DATA_FILE, 'r') as f:
        data = json.load(f)
        return CitiesData(**data)

def write_cities(cities_data: CitiesData):
    """Write cities to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(cities_data.dict(), f, indent=2)

def generate_id() -> str:
    """Generate a short unique ID similar to the format in your example"""
    return uuid.uuid4().hex[:4]

# API Endpoints
@router.get("/cities")
async def get_cities():
    """Get all cities"""
    try:
        cities_data = read_cities()
        return cities_data.cities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cities/{city_id}")
async def get_city(city_id: str):
    """Get a single city by ID"""
    try:
        cities_data = read_cities()
        city = next((c for c in cities_data.cities if c.id == city_id), None)
        
        if city is None:
            raise HTTPException(status_code=404, detail="City not found")
        
        return city
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cities", response_model=City)
async def create_city(city_data: CityCreate):
    """Create a new city"""
    try:
        cities_data = read_cities()
        
        # Generate a unique ID
        new_id = generate_id()
        # Ensure ID is unique
        while any(c.id == new_id for c in cities_data.cities):
            new_id = generate_id()
        
        # Create the city with the generated ID
        new_city = City(
            id=new_id,
            cityName=city_data.cityName,
            country=city_data.country,
            emoji=city_data.emoji,
            date=city_data.date,
            notes=city_data.notes,
            position=city_data.position
        )
        
        cities_data.cities.append(new_city)
        write_cities(cities_data)
        
        return new_city
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cities/{city_id}")
async def delete_city(city_id: str):
    """Delete a city by ID"""
    try:
        cities_data = read_cities()
        
        # Find and remove the city
        original_length = len(cities_data.cities)
        cities_data.cities = [c for c in cities_data.cities if c.id != city_id]
        
        if len(cities_data.cities) == original_length:
            raise HTTPException(status_code=404, detail="City not found")
        
        write_cities(cities_data)
        
        return {"message": "City deleted successfully", "id": city_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Cities API is running"}
