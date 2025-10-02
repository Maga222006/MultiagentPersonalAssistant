from dotenv import load_dotenv
from github import Github
import os

load_dotenv()

def list_repos():
    """Lists all repositories owned by the authenticated GitHub user."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repos = user.get_repos()
        repo_names = [repo.name for repo in repos]
        return ', '.join(repo_names)
    except Exception as e:
        return None

def download_repo(project_name: str, repo_owner: str = None, branch: str = "main", private: bool = False):
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
        user.create_repo(project_name, private=private)
    else:
        repo = user.get_repo(project_name)

    dest_path = os.path.join('agents/coder/projects', project_name)
    os.makedirs(dest_path, exist_ok=True)

    try:
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
    except Exception as e:
        return f"Error downloading repository: {str(e)}"

def initialize_project(project_name: str, repo_owner: str = None, branch: str = "main", private: bool = False):
    """Creates a project directory and GitHub repository with the given project_name."""
    try:
        github = Github(os.getenv('GITHUB_TOKEN'))
        user = github.get_user()
        repos = user.get_repos()
        repo_names = [repo.name for repo in repos]
        if project_name in repo_names or repo_owner:
            try:
                download_repo(project_name=project_name, repo_owner=repo_owner, branch=branch, private=private)
                return f"Repository '{f'{repo_owner}/{project_name}' if repo_owner else project_name}' downloaded successfully!"
            except Exception as e:
                os.mkdir(f"agents/coder/projects/{project_name}")
                user.create_repo(project_name, private=private)
                return f"Repository '{project_name}' created successfully!"
        else:
            user.create_repo(project_name, private=private)
            os.mkdir(f"agents/coder/projects/{project_name}")
            return f"Repository '{project_name}' created successfully!"
    except Exception as e:
        return f"Error creating repository: {str(e)}"