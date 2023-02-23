import re
from urllib.parse import urlparse

import boto3

from botocore.exceptions import BotoCoreError
from cleo.io.io import IO
from poetry.config.config import Config
from poetry.exceptions import PoetryException
from poetry.plugins import Plugin
from poetry.poetry import Poetry
from poetry.utils.authenticator import Authenticator

RE_CODEARTIFACT_NETLOC = re.compile(
    r"^([a-z][a-z-]*)-(\d+)\.d\.codeartifact\.[^.]+\.amazonaws\.com$"
)


def monkeypatch_authenticator(io: IO):
    old_request = Authenticator.request

    def new_request(self: Authenticator, method, url, *args, **kwargs):
        new_kwargs = kwargs.copy()
        raise_for_status = new_kwargs.pop("raise_for_status", None)
        new_kwargs["raise_for_status"] = False

        response = old_request(self, method, url, *args, **new_kwargs)

        if response.status_code in (401, 403):
            netloc = urlparse(response.url)[1]
            if m := RE_CODEARTIFACT_NETLOC.match(netloc):
                domain, domain_owner = m.groups()
                if config := self.get_repository_config_for_url(url):
                    io.write_line(
                        f"Getting new CodeArtifact authorization token for repo {config.name} ({domain=}, {domain_owner=})..."
                    )
                    try:
                        response = boto3.client("codeartifact").get_authorization_token(
                            domain=domain,
                            domainOwner=domain_owner,
                        )
                    except BotoCoreError as err:
                        raise PoetryException(
                            f"Failed to get a new CodeArtifact authorization token: {err}\n\n-> Are your local AWS credentials up-to-date?"
                        )
                    self._password_manager.set_http_password(
                        config.name, "aws", response["authorizationToken"]
                    )
                    self.reset_credentials_cache()
                    self._password_manager._config = Config.create(reload=True)

                    # Retry the request now that we're authenticated
                    return old_request(self, method, url, *args, **kwargs)

        if raise_for_status:
            response.raise_for_status()
        return response

    Authenticator.request = new_request


class CodeArtifactPlugin(Plugin):
    def activate(self, poetry: Poetry, io: IO) -> None:
        monkeypatch_authenticator(io)
