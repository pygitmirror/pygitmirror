"""The services which hold repositories: where their git data is, and their API."""

from pygitmirror.hosts._factory import PROVIDERS, make_host
from pygitmirror.hosts.api_client import ApiClient
from pygitmirror.hosts.api_response import ApiResponse
from pygitmirror.hosts.bitbucket_host import BitbucketHost
from pygitmirror.hosts.gitea_host import GiteaHost
from pygitmirror.hosts.github_host import GitHubHost
from pygitmirror.hosts.github_style_host import GitHubStyleHost
from pygitmirror.hosts.gitlab_host import GitLabHost
from pygitmirror.hosts.host import Host
from pygitmirror.hosts.plain_host import PlainHost
from pygitmirror.hosts.repository_info import RepositoryInfo

__all__ = [
    "PROVIDERS",
    "ApiClient",
    "ApiResponse",
    "BitbucketHost",
    "GitHubHost",
    "GitHubStyleHost",
    "GitLabHost",
    "GiteaHost",
    "Host",
    "PlainHost",
    "RepositoryInfo",
    "make_host",
]
