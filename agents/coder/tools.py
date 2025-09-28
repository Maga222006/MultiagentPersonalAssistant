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
def create_project(project_name: str, private: bool = False):
    """Creates a project directory and GitHub repository with the given project_name."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        user.create_repo(project_name, private=private)
        os.mkdir(f"agents/coder/projects/{project_name}")
        return f"Repository '{project_name}' created successfully!"
    except Exception as e:
        return f"Error creating repository: {str(e)}"

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
        with open(f"agents/coder/projects/{project_name}/{file_path}", "w", encoding="utf-8") as f:
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
        if os.path.isfile(file_path):
            os.remove(file_path)
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
def read_repo_file(project_name: str, file_path: str):
    """Reads the content of a file from a GitHub repository."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repo = user.get_repo(project_name)
        file = repo.get_contents(file_path)
        return file.decoded_content.decode('utf-8')
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def read_file(project_name: str, file_path: str) -> str:
    """Reads the content of a file from a project directory."""
    full_path = f"agents/coder/projects/{project_name}/{file_path}"
    try:
        with open(full_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file '{full_path}': {str(e)}"

@tool
def list_repo_files(project_name: str):
    """Lists all files in the GitHub repository."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repo = user.get_repo(project_name)
        files = repo.get_contents("")
        file_list = [file.name for file in files]
        return f"Files in '{project_name}': {', '.join(file_list)}"
    except Exception as e:
        return f"Error listing files: {str(e)}"

@tool
def list_files(project_name: str, directory: str = "") -> dict:
    """
    Lists files in a project directory.

    :param project_name: Name of the project.
    :param directory: Optional subdirectory inside the project. By default, all project files are listed.
    :return: List of files in the directory inside the project.
    """
    base_path = os.path.join("agents/coder/projects", project_name, directory)

    try:
        if not os.path.exists(base_path):
            return f"Directory '{base_path}' does not exist."

        if not os.path.isdir(base_path):
            return f"Path '{base_path}' is not a directory."

        files = os.listdir(base_path)
        return files

    except Exception as e:
        return f"Error listing files: {str(e)}"

@tool
def run_cmd(project_name: str, cmd: str, timeout: int = 30):
    """
    Runs a shell command in the project_name directory.
    """
    project_dir = os.path.join("agents/coder/projects", project_name)

    if not os.path.isdir(project_dir):
        return -1, "", f"Project directory not found: {project_dir}"

    try:
        res = subprocess.run(
            cmd,
            shell=True,
            cwd=project_dir,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired as e:
        return -1, e.stdout or "", f"Command timed out after {timeout}s"
    except Exception as e:
        return -1, "", f"Error running command: {str(e)}"

@tool
def download_repo(project_name: str, repo_owner: str = None, branch: str = "main"):
    """
    Downloads a GitHub repo (user/<project_name>) using PyGithub
    and saves it into agents/coder/projects/{project_name}.

    Args:
        project_name (str): Repo name on GitHub and local folder name.
        repo_owner (str): Repo owner on GitHub, by default = None (it's the user's repository).
        branch (str): Branch to download (default 'main').
    """
    gh = Github(os.getenv("GITHUB_TOKEN"))
    user = gh.get_user()
    if repo_owner:
        repo = gh.get_repo(f"{repo_owner}/{project_name}")
    else:
        repo = user.get_repo(project_name)

    dest_path = os.path.join('agents/coder/projects', project_name)
    os.makedirs(dest_path, exist_ok=True)

    branch_ref = repo.get_branch(branch)
    commit_sha = branch_ref.commit.sha

    # Get the tree (recursive = True to walk full repo)
    tree = repo.get_git_tree(commit_sha, recursive=True).tree

    for item in tree:
        file_path = os.path.join(dest_path, item.path)

        if item.type == "tree":
            os.makedirs(file_path, exist_ok=True)
        elif item.type == "blob":
            blob = repo.get_git_blob(item.sha)
            file_content = blob.content
            import base64
            decoded = base64.b64decode(file_content)

            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(decoded)

    return f"Repo '{project_name}' downloaded into {dest_path}."

tools = [tavily_search, create_project, list_repos, list_repo_branches, create_repo_branch, write_file, delete_file, read_repo_file, read_file, list_repo_files, list_files, run_cmd, download_repo]
