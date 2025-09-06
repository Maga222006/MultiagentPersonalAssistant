from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from langchain_community.utilities import OpenWeatherMapAPIWrapper
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun
from langchain_tavily.tavily_search import TavilySearch
from timezonefinder import TimezoneFinder
from langchain_core.tools import tool
from dotenv import load_dotenv
from geopy import Nominatim
from github import Github
import datetime
import pytz
import os

load_dotenv()

wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
yahoo = YahooFinanceNewsTool()
web_search = TavilySearch(
    max_results=5,
    topic="general",
    include_answer=True
)
tf = TimezoneFinder()
geolocator = Nominatim(user_agent="my_geocoder")
weekday_mapping = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")

@tool
def create_repo(repo_name: str, private: bool = False):
    """Creates a GitHub repository with the given repo_name."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        user.create_repo(repo_name, private=private)
        return f"Repository '{repo_name}' created successfully!"
    except Exception as e:
        return f"Error creating repository: {str(e)}"

@tool
def commit_file_to_repo(repo_name: str, file_path: str, file_contents: str):
    """Adds a new file to the GitHub repository or updates the existing one."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repo = user.get_repo(repo_name)

        try:
            # Check if file exists
            file = repo.get_contents(file_path)
            sha = file.sha
            repo.update_file(file_path, "Updating file", file_contents, sha)
            return f"File '{file_path}' updated successfully in '{repo_name}'."
        except:
            repo.create_file(file_path, "Adding new file", file_contents)
            return f"File '{file_path}' created successfully in '{repo_name}'."
    except Exception as e:
        return f"Error with file operation: {str(e)}"

@tool
def read_file(repo_name: str, file_path: str):
    """Reads the content of a file from a GitHub repository."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repo = user.get_repo(repo_name)
        file = repo.get_contents(file_path)
        return file.decoded_content.decode('utf-8')
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def list_repos():
    """Lists all repositories owned by the authenticated GitHub user."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repos = user.get_repos()
        repo_names = [repo.name for repo in repos]
        return f"Repositories: {', '.join(repo_names)}"
    except Exception as e:
        return f"Error listing repositories: {str(e)}"

@tool
def list_files(repo_name: str):
    """Lists all files in the GitHub repository."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repo = user.get_repo(repo_name)
        files = repo.get_contents("")
        file_list = [file.name for file in files]
        return f"Files in '{repo_name}': {', '.join(file_list)}"
    except Exception as e:
        return f"Error listing files: {str(e)}"

@tool
def delete_file(repo_name: str, file_path: str):
    """Deletes a file from the GitHub repository."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repo = user.get_repo(repo_name)
        file = repo.get_contents(file_path)
        sha = file.sha
        repo.delete_file(file_path, "Deleting file", sha)
        return f"File '{file_path}' deleted successfully from '{repo_name}'."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

@tool
def list_branches(repo_name: str):
    """Lists all branches in a GitHub repository."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repo = user.get_repo(repo_name)
        branches = repo.get_branches()
        branch_names = [branch.name for branch in branches]
        return f"Branches in '{repo_name}': {', '.join(branch_names)}"
    except Exception as e:
        return f"Error listing branches: {str(e)}"

@tool
def create_branch(repo_name: str, branch_name: str):
    """Creates a new branch in a GitHub repository."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repo = user.get_repo(repo_name)
        main_branch = repo.get_branch("main")
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)
        return f"Branch '{branch_name}' created successfully in '{repo_name}'."
    except Exception as e:
        return f"Error creating branch: {str(e)}"

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

coder_tools = [web_search, create_repo, create_branch, commit_file_to_repo, read_file, list_files, list_repos, list_branches, delete_file]
supervisor_tools = [yahoo, web_search, current_time, weather]
deep_research_tools = [web_search, yahoo, wikipedia]
