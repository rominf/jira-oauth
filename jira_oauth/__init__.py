from configparser import ConfigParser
from pathlib import Path
from typing import Union, Optional, Tuple
from urllib import parse
import base64

from tlslite.utils import keyfactory
import oauth2 as oauth


PathOrStr = Union[Path, str]


class JiraOAuth:
    oauth_config_dir_path = Path.home() / '.oauthconfig'
    starter_oauth_config_file = oauth_config_dir_path / 'starter_oauth.config'
    rsa_private_key_file_path = oauth_config_dir_path / 'oauth.pem'
    rsa_public_key_file_path = oauth_config_dir_path / 'oauth.pub'

    # noinspection PyPep8Naming
    class SignatureMethod_RSA_SHA1(oauth.SignatureMethod):
        name = 'RSA-SHA1'

        def __init__(self, rsa_private_key: str):
            self.rsa_private_key = rsa_private_key.strip()

        def signing_base(self, request: oauth.Request, consumer: oauth.Consumer, token: oauth.Token) -> Tuple[str, str]:
            if not hasattr(request, 'normalized_url') or request.normalized_url is None:
                raise ValueError("Base URL for request is not set.")

            sig = (
                oauth.escape(request.method),
                oauth.escape(request.normalized_url),
                oauth.escape(request.get_normalized_parameters()),
            )

            key = f'oauth.escape(consumer.secret)&{oauth.escape(token.secret) if token else ""}'
            raw = '&'.join(sig)
            return key, raw

        def sign(self, request: oauth.Request, consumer: oauth.Consumer, token: oauth.Token) -> bytes:
            """Builds the base signature string."""
            key, raw = self.signing_base(request=request, consumer=consumer, token=token)
            private_key = keyfactory.parsePrivateKey(self.rsa_private_key)
            signature = private_key.hashAndSign(bytes=bytearray(raw, 'utf8'))

            return base64.b64encode(signature)

    def __init__(self, consumer_key: Optional[str] = None, jira_url: Optional[str] = None,
                 rsa_private_key: Optional[str] = None, rsa_public_key: Optional[str] = None,
                 test_jira_issue: Optional[str] = None):
        self.consumer_key = consumer_key
        self.jira_base_url = jira_url
        self.rsa_private_key = rsa_private_key
        self.rsa_public_key = rsa_public_key
        self.test_jira_issue = test_jira_issue
        self.consumer = None
        self.request_token = None
        self.url = None
        self.access_token = {}

    @classmethod
    def from_file(cls) -> 'JiraOAuth':
        self = cls()
        self.read_jira_oauth_init_parameters_from_file()
        return self

    @property
    def _access_token_url(self) -> str:
        return f'{self.jira_base_url}/plugins/servlet/oauth/access-token'

    @property
    def data_url(self) -> str:
        return f'{self.jira_base_url}/rest/api/2/issue/{self.test_jira_issue}?fields=summary'

    @staticmethod
    def _read_file(path: PathOrStr) -> str:
        with open(file=str(path), mode='r') as f:
            return f.read()

    def read_jira_oauth_init_parameters_from_file(self) -> None:
        config = ConfigParser()
        config.optionxform = str  # Read config file as case insensitive
        config.read(self.starter_oauth_config_file)

        self.consumer_key = config.get("oauth_config", "consumer_key")
        self.jira_base_url = config.get("oauth_config", "jira_base_url")
        self.rsa_private_key = self._read_file(path=self.rsa_private_key_file_path)
        self.rsa_public_key = self._read_file(path=self.rsa_public_key_file_path)
        self.test_jira_issue = config.get("oauth_config", "test_jira_issue")

    def generate_request_token_and_auth_url(self) -> None:
        request_token_url = f'{self.jira_base_url}/plugins/servlet/oauth/request-token'
        authorize_url = f'{self.jira_base_url}/plugins/servlet/oauth/authorize'

        self.consumer = oauth.Consumer(key=self.consumer_key, secret=self.rsa_public_key)
        client = oauth.Client(consumer=self.consumer)
        client.set_signature_method(JiraOAuth.SignatureMethod_RSA_SHA1(rsa_private_key=self.rsa_private_key))

        # Step 1: Get a request token. This is a temporary token that is used for
        # having the user authorize an access token and to sign the request to obtain
        # said access token.
        resp, content = client.request(request_token_url, "POST")
        if resp['status'] != '200':
            raise Exception("Invalid response %s: %s" % (resp['status'], content))

        # If output is in bytes. Let's convert it into String.
        if type(content) == bytes:
            content = content.decode('UTF-8')

        self.request_token = dict(parse.parse_qsl(content))
        self.url = f"{authorize_url}?oauth_token={self.request_token['oauth_token']}"

    def generate_access_token(self):
        # Step 3: Once the consumer has redirected the user back to the oauth_callback
        # URL you can request the access token the user has approved. You use the
        # request token to sign this request. After this is done you throw away the
        # request token and use the access token returned. You should store this
        # access token somewhere safe, like a database, for future use.
        token = oauth.Token(key=self.request_token['oauth_token'], secret=self.request_token['oauth_token_secret'])
        # token.set_verifier(oauth_verifier)
        client = oauth.Client(consumer=self.consumer, token=token)
        client.set_signature_method(JiraOAuth.SignatureMethod_RSA_SHA1(rsa_private_key=self.rsa_private_key))

        resp, content = client.request(uri=self._access_token_url, method="POST")
        # Response is coming in bytes. Let's convert it into String.
        # If output is in bytes. Let's convert it into String.
        if type(content) == bytes:
            content = content.decode('UTF-8')
        self.access_token = dict(parse.parse_qsl(qs=content))

