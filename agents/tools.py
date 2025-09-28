from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from langchain_community.utilities import OpenWeatherMapAPIWrapper
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun
from langchain_tavily.tavily_search import TavilySearch
from agents.coder.agent import coder_agent
from agents.utils.smart_home import change_device_states
from timezonefinder import TimezoneFinder
from langchain_core.tools import tool
from dotenv import load_dotenv
from geopy import Nominatim
import datetime
import pytz
import os

load_dotenv()


tf = TimezoneFinder()
web_search = TavilySearch(
    max_results=5,
    topic="general",
    include_answer=True
)
yahoo = YahooFinanceNewsTool()
geolocator = Nominatim(user_agent="my_geocoder")
wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
weekday_mapping = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

@tool
def current_time(location: str = None):
    """Get the current time for a location or current position."""
    try:
        if location:
            location_data = geolocator.geocode(location)
            if location_data:
                timezone = pytz.timezone(tf.timezone_at(lat=location_data.latitude, lng=location_data.longitude))
                location_name = location.capitalize()
            else:
                return f"Could not find location: {location}"
        else:
            # Use environment location if available
            lat = os.getenv('LATITUDE')
            lon = os.getenv('LONGITUDE')
            if lat and lon:
                timezone = pytz.timezone(tf.timezone_at(lat=float(lat), lng=float(lon)))
                location_name = os.getenv('LOCATION', 'Current Location')
            else:
                timezone = pytz.UTC
                location_name = 'UTC'

        current_dt = datetime.datetime.now(timezone)
        weekday = weekday_mapping[current_dt.weekday()]
        return f"Location: {location_name}; Current Date and Time: {current_dt.strftime('%Y-%m-%d %H:%M')}, {weekday}."
    except Exception as e:
        return f"Error getting current time: {str(e)}"

@tool
def weather(location: str = None):
    """Get the current weather for a location or current position."""
    try:
        weather_wrapper = OpenWeatherMapAPIWrapper(
            openweathermap_api_key=os.getenv('OPENWEATHERMAP_API_KEY')
        )
        if not location:
            location = os.getenv('LOCATION', 'Unknown')
        return weather_wrapper.run(location=location)
    except Exception as e:
        return f"Error getting weather: {str(e)}"


tools = [yahoo, web_search, current_time, weather, change_device_states, coder_agent]


