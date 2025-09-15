from langchain_community.tools.yahoo_finance_news import YahooFinanceNewsTool
from langchain_community.utilities import OpenWeatherMapAPIWrapper
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_community.tools import WikipediaQueryRun
from langchain_tavily.tavily_search import TavilySearch
from timezonefinder import TimezoneFinder
from langchain_core.tools import tool
from tuya_iot import TuyaOpenAPI
from dotenv import load_dotenv
from geopy import Nominatim
from github import Github
import phonenumbers
import pycountry
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
endpoint_map = {
    "https://openapi.tuyacn.com": [86],
    "https://openapi.tuyain.com": [91],
    "https://openapi.tuyaus.com": [1, 51, 52, 54, 55, 56, 57, 58, 81, 82, 239,
                                   245, 502, 591, 593, 595, 597, 598, 674, 678, 682, 683, 685, 686, 690, 970,
                                   1340, 1684, 1670, 1671, 1787, 1809, 1829, 1849, 5999, 35818, 64],
    "https://openapi.tuyaeu.com": [7, 20, 27, 30, 31, 32, 33, 34, 36, 39, 40,
                                   90, 92, 93, 94, 212, 213, 216, 218, 220, 221, 222, 223, 224, 225, 226, 227,
                                   228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 240, 241, 242, 243,
                                   244, 246, 248, 250, 251, 252, 253, 254, 255, 256, 257, 258, 260, 261, 262,
                                   263, 264, 265, 266, 267, 268, 269, 291, 297, 298, 299, 350, 351, 352, 353,
                                   354, 355, 356, 357, 358, 359, 370, 371, 372, 373, 374, 375, 376, 377, 378,
                                   379, 380, 381, 382, 385, 386, 387, 389, 420, 421, 423, 500, 501, 503, 504,
                                   505, 506, 507, 508, 509, 590, 592, 594, 596, 672, 676, 679, 680, 681, 687,
                                   688, 689, 691, 692, 960, 961, 962, 964, 965, 966, 967, 968, 971, 972, 973,
                                   974, 975, 976, 977, 992, 993, 994, 995, 996, 998, 1242, 1246, 1264, 1268,
                                   1284, 1345, 1441, 1473, 1649, 1664, 1721, 1758, 1767, 1784, 1868, 1869,
                                   1876, 4779, 61, 880, 41, 43, 44, 45, 46, 47, 48, 49],
    "https://openapi-sg.iotbing.com": [84, 856, 855, 66, 95, 60, 65, 62, 63,
                                       673, 670, 675, 677, 852, 853, 886],
}
country = pycountry.countries.lookup(os.getenv('TUYA_COUNTRY').title())
country_code = phonenumbers.country_code_for_region(country.alpha_2)
for endpoint, country_codes in endpoint_map.items():
    if country_code in country_codes:
        os.environ['TUYA_COUNTRY_CODE'] = str(country_code)
        os.environ['TUYA_ENDPOINT'] = endpoint
        break
openapi = TuyaOpenAPI(os.getenv('TUYA_ENDPOINT'), os.getenv('TUYA_ACCESS_ID'), os.getenv('TUYA_ACCESS_KEY'))
connection = openapi.connect(os.getenv('TUYA_USERNAME'), os.getenv('TUYA_PASSWORD'), os.getenv('TUYA_COUNTRY_CODE'), 'TuyaSmart')
if not connection['success']:
    connection = openapi.connect(os.getenv('TUYA_USERNAME'), os.getenv('TUYA_PASSWORD'), os.getenv('TUYA_COUNTRY_CODE'), 'SmartLife')
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

@tool
def get_device_list():
    """
    Get the list of devices bound to the smart home.
    Each device has id: str, name: str and states: List[dict].
    States is a list of device states which can be changed.
    State format: {'code': ..., 'value': ...}
    """
    response = openapi.get('/v1.0/users/{}/devices'.format(connection['result']['uid']))['result']
    devices = []
    for device in response:
        devices.append({"id": device['id'], 'name': device['name'], 'states': device['status']})
    return devices

@tool
def change_device_states(id:str, commands:list[dict]):
    """
    Control the smart home devices by sending commands.
    Accepts device id:str and a list of commands: List[dict].
    Commands is a list of changed device states.
    State format: {'code': ..., 'value': ...}
    """
    response = openapi.post('/v1.0/devices/{}/commands'.format(id), {"commands": commands})
    return "success" if response["success"] else "failure"

coder_tools = [web_search, create_repo, create_branch, commit_file_to_repo, read_file, list_files, list_repos, list_branches, delete_file]
supervisor_tools = [yahoo, web_search, current_time, weather]
deep_research_tools = [web_search, yahoo, wikipedia]
smart_home_tools = [get_device_list, change_device_states]
