from typing import TypedDict, List
from pydantic import Field

class SearchQuery(TypedDict):
    query: str = Field(description="A single plain text search query string.")

class PlanResearch(TypedDict):
    search_queries: List[SearchQuery] = Field(description="A list of search queries, to find all the info user asked for. Break user query down into smaller search queries.")

class PlanCodingTask(TypedDict):
    repo_name: str = Field(description="The name of the GitHub repository for the project.")
    private: bool = Field(description="Whether or not the repository is private.", default=False)
    task_description: str = Field(description="A detailed description of the project for the coder to create.")