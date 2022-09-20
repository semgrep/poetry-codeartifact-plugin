# poetry-codeartifact-plugin

This Poetry plugin automatically refreshes your authorization token when working with CodeArtifact repositories.

## Installation

Run this to install the plugin:
`poetry self add poetry-codeartifact-plugin`

And to remove:
`poetry self remove poetry-codeartifact-plugin`

## Usage

No configuration or workflow changes are needed. If the plugin detects a HTTP 401 or 403 from a CodeArtifact URL, it will refresh your authorization token and retry the request.

This assumes that your local AWS creds are up-to-date -- if not, your command will still fail.


## Adding a CodeArtifact repository

Add this snippet to your project's `pyproject.toml`:

```toml
[[tool.poetry.source]]
name = "codeartifact-pypi"  # arbitrary, just don't reuse repository names between CodeArtifact repos
url = "https://DOMAIN-123412341234.d.codeartifact.us-west-2.amazonaws.com/REPO/pypi/simple/"  # get this URL from your CodeArtifact dashboard or the GetRepositoryEndpoint API call
```

Learn more about Poetry repositories here: https://python-poetry.org/docs/repositories/