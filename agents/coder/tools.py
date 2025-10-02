from langchain_tavily import TavilySearch
from langchain_core.tools import tool
from dotenv import load_dotenv
from github import Github
import subprocess
import os

load_dotenv()

tavily_search = TavilySearch(
    max_results=5,
    topic="general",
    include_answer=False
)

@tool
def list_repo_branches(project_name: str):
    """Lists all branches in a GitHub repository."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repo = user.get_repo(project_name)
        branches = repo.get_branches()
        branch_names = [branch.name for branch in branches]
        return f"Branches in '{project_name}': {', '.join(branch_names)}"
    except Exception as e:
        return f"Error listing branches: {str(e)}"

@tool
def create_repo_branch(project_name: str, branch_name: str):
    """Creates a new branch in a GitHub repository."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repo = user.get_repo(project_name)
        main_branch = repo.get_branch("main")
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)
        return f"Branch '{branch_name}' created successfully in '{project_name}'."
    except Exception as e:
        return f"Error creating branch: {str(e)}"

@tool
def write_file(project_name: str, file_path: str, file_contents: str):
    """Adds a new file to the project directory and GitHub repository or updates the existing one."""
    try:
        full_path = os.path.join('agents/coder/projects', project_name, file_path)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(file_contents)
    except Exception as e:
        return f"Error with file operation: {str(e)}"
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repo = user.get_repo(project_name)

        try:
            # Check if file exists
            file = repo.get_contents(file_path)
            sha = file.sha
            repo.update_file(file_path, "Updating file", file_contents, sha)
            return f"File '{file_path}' updated successfully in '{project_name}'."
        except:
            repo.create_file(file_path, "Adding new file", file_contents)
            return f"File '{file_path}' created successfully in '{project_name}'."
    except Exception as e:
        return f"Error with file operation: {str(e)}"

@tool
def delete_file(project_name: str, file_path: str):
    """Deletes a file from the GitHub repository."""
    try:
        full_path = os.path.join('agents/coder/projects', project_name, file_path)
        if os.path.isfile(full_path):
            os.remove(full_path)
    except Exception as e:
        return f"Error deleting file: {str(e)}"
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repo = user.get_repo(project_name)
        file = repo.get_contents(file_path)
        sha = file.sha
        repo.delete_file(file_path, "Deleting file", sha)
        return f"File '{file_path}' deleted successfully from '{project_name}'."
    except Exception as e:
        return f"Error deleting file: {str(e)}"

@tool
def read_file(project_name: str, file_path: str) -> str:
    """Reads the content of a file from a project directory."""
    full_path = os.path.join('agents/coder/projects', project_name, file_path)
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file '{full_path}': {str(e)}"

@tool
def list_files(project_name: str, directory: str = "") -> dict:
    """
    Lists files in a project directory.

    :param project_name: The name of the project.
    :param directory: Optional subdirectory inside the project. By default, (directory="") all project files are listed.
    :return: List of files in the directory inside the project.
    """
    full_path = os.path.join('agents/coder/projects', project_name, directory)
    try:
        if not os.path.exists(full_path):
            return f"Directory '{full_path}' does not exist."

        if not os.path.isdir(full_path):
            return f"Path '{full_path}' is not a directory."

        files = os.listdir(full_path)
        return files

    except Exception as e:
        return f"Error listing files: {str(e)}"

@tool
def run_cmd(project_name: str, cmd: str, timeout: int = 30):
    """
    Runs a shell command in the project_name directory.
    """
    full_path = os.path.join("agents/coder/projects", project_name)

    if not os.path.isdir(full_path):
        return -1, "", f"Project directory not found: {full_path}"

    try:
        res = subprocess.run(
            cmd,
            shell=True,
            cwd=full_path,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired as e:
        return -1, e.stdout or "", f"Command timed out after {timeout}s"
    except Exception as e:
        return -1, "", f"Error running command: {str(e)}"


tools = [tavily_search, list_repo_branches, create_repo_branch, write_file, delete_file, read_file, list_files, run_cmd]
