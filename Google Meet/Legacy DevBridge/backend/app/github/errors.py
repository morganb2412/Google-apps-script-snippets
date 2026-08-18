class GitHubIntegrationError(RuntimeError):
    pass


class GitHubConnectionExpiredError(GitHubIntegrationError):
    pass


class GitHubResourceNotFoundError(GitHubIntegrationError):
    pass


class GitHubUnavailableError(GitHubIntegrationError):
    pass
