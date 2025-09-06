from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from database_interaction.models import User, Base
from sqlalchemy.orm import sessionmaker
from geopy.geocoders import Nominatim
from dotenv import load_dotenv
import os

load_dotenv()
# Ensure SQLite URL is used, override any PostgreSQL URL from environment  
DATABASE_URL = "sqlite+aiosqlite:///./database_files/main.db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
geolocator = Nominatim(user_agent="ai_assistant")

def get_location_name(lat: float, lon: float) -> str:
    """Get location name from coordinates"""
    try:
        location = geolocator.reverse((lat, lon), language='en')
        if location and location.raw and 'address' in location.raw:
            address = location.raw['address']
            return (
                address.get('city')
                or address.get('town')
                or address.get('village')
                or address.get('municipality')
                or address.get('county')
                or "Unknown"
            )
        return "Unknown"
    except Exception as e:
        print(f"[Geocoding Error] {e}")
        return "Unknown"

async def init_user_db():
    """Initialize user database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def create_or_update_user(user_id: str, first_name: str = None, last_name: str = None,
                                latitude: float = None, longitude: float = None):
    """Create or update user information
    :rtype: None
    """
    location_name = get_location_name(latitude, longitude) if latitude and longitude else None
    async with AsyncSessionLocal() as session:
        async with session.begin():
            user = await session.get(User, user_id)
            if user:
                if first_name is not None:
                    user.first_name = first_name
                if last_name is not None:
                    user.last_name = last_name
                if latitude is not None:
                    user.latitude = latitude
                if longitude is not None:
                    user.longitude = longitude
                if location_name is not None:
                    user.location = location_name
            else:
                user = User(
                    user_id=user_id,
                    first_name=first_name,
                    last_name=last_name,
                    latitude=latitude,
                    longitude=longitude,
                    location=location_name
                )
                session.add(user)
        await session.commit()

async def get_user_by_id(user_id: str):
    """Get user by ID"""
    async with AsyncSessionLocal() as session:
        result = await session.get(User, user_id)
        if result:
            return {
                "user_id": user_id,
                "first_name": result.first_name,
                "last_name": result.last_name,
                "latitude": result.latitude,
                "longitude": result.longitude,
                "location": result.location
            }
        return {
            "user_id": user_id,
            "first_name": None,
            "last_name": None,
            "latitude": None,
            "longitude": None,
            "location": None
        }
