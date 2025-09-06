from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from database_interaction.models import UserConfig, Base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_async_engine("sqlite+aiosqlite:///./database_files/main.db", echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_config_db():
    """Initialize config database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def create_or_update_config(user_id: str, **kwargs):
    """Create or update user configuration"""
    async with AsyncSessionLocal() as session:
        async with session.begin():
            config = await session.get(UserConfig, user_id)
            if config:
                for key, value in kwargs.items():
                    if hasattr(config, key) and value is not None:
                        setattr(config, key, value)
            else:
                # Filter out None values for new config
                filtered_kwargs = {k: v for k, v in kwargs.items() if v is not None}
                config = UserConfig(user_id=user_id, **filtered_kwargs)
                session.add(config)
        await session.commit()


async def get_config_by_user_id(user_id: str):
    """Get configuration by user ID"""
    async with AsyncSessionLocal() as session:
        config = await session.get(UserConfig, user_id)
        if config:
            return {key: getattr(config, key) for key in config.__table__.columns.keys()}
        return None


async def load_config_to_env(user_id: str):
    """Load user configuration to environment variables"""
    config = await get_config_by_user_id(user_id)
    if not config:
        return

    # Map config keys to environment variable names
    env_mapping = {
        'assistant_name': 'ASSISTANT_NAME',
        'openweathermap_api_key': 'OPENWEATHERMAP_API_KEY',
        'github_token': 'GITHUB_TOKEN',
        'tavily_api_key': 'TAVILY_API_KEY',
        'groq_api_key': 'GROQ_API_KEY',
    }

    for config_key, env_key in env_mapping.items():
        value = config.get(config_key)
        if value is not None:
            os.environ[env_key] = str(value)


async def save_env_to_file():
    """Save current environment variables to .env file"""
    env_vars = [
        'DATABASE_URL', 'TOKEN', 'ASSISTANT_NAME', 'LOCATION', 'LATITUDE', 'LONGITUDE',
        'OPENWEATHERMAP_API_KEY', 'GITHUB_TOKEN', 'TAVILY_API_KEY',
        'GROQ_API_KEY'
    ]

    # Set default values if not present
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'sqlite+aiosqlite:///./database_files/main.db'
    if not os.getenv('TOKEN'):
        os.environ['TOKEN'] = '7456008559:AAFbid5x8hhM4qe70SW9xyDHaiDCwHjkQH4'

    with open('.env', 'w') as f:
        for var in env_vars:
            value = os.getenv(var, '')
            f.write(f"{var}={value}\n")