from configparser import ConfigParser
from pathlib import Path
from typing import Union, Optional, Tuple
from urllib import parse
import asyncio
import base64

from aiohttp.web_app import Application
from aiohttp.web_exceptions import HTTPOk
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from tlslite.utils import keyfactory
from yarl import URL
import aioauth2
import oauth2


PathOrStr = Union[Path, str]


class JiraOAuth:
    AUTH_RESPONSE_TEXT_DEFAULT = ('<!DOCTYPE html><html>'
            '<head><script type="text/javascript">window.close()</script></head>'
            '<body>Authorization was successful. You can close this page now.</body></html>')

    oauth_config_dir_path = Path.home() / '.oauthconfig'
    starter_oauth_config_file = oauth_config_dir_path / 'starter_oauth.config'
    rsa_private_key_file_path = oauth_config_dir_path / 'oauth.pem'
    rsa_public_key_file_path = oauth_config_dir_path / 'oauth.pub'

    # noinspection PyPep8Naming
    class SignatureMethod_RSA_SHA1(oauth2.SignatureMethod):
        name = 'RSA-SHA1'

        def __init__(self, rsa_private_key: str):
            self.rsa_private_key = rsa_private_key.strip()

        def signing_base(self, request: oauth2.Request, consumer: oauth2.Consumer,
                         token: oauth2.Token) -> Tuple[str, str]:
            if not hasattr(request, 'normalized_url') or request.normalized_url is None:
                raise ValueError("Base URL for request is not set.")

            sig = (
                oauth2.escape(request.method),
                oauth2.escape(request.normalized_url),
                oauth2.escape(request.get_normalized_parameters()),
            )

            key = f'oauth.escape(consumer.secret)&{oauth2.escape(token.secret) if token else ""}'
            raw = '&'.join(sig)
            return key, raw

        def sign(self, request: oauth2.Request, consumer: oauth2.Consumer, token: oauth2.Token) -> bytes:
            """Builds the base signature string."""
            key, raw = self.signing_base(request=request, consumer=consumer, token=token)
            private_key = keyfactory.parsePrivateKey(self.rsa_private_key)
            # noinspection PyArgumentList
            signature = private_key.hashAndSign(bytes=bytearray(raw, 'utf8'))

            return base64.b64encode(signature)

    def __init__(self, consumer_key: Optional[str] = None, jira_url: Optional[str] = None,
                 rsa_private_key: Optional[str] = None, rsa_public_key: Optional[str] = None,
                 test_jira_issue: Optional[str] = None, redirect_url: Optional[str] = None,
                 app: Optional[Application] = None, auth_response_text: str = AUTH_RESPONSE_TEXT_DEFAULT,
                 loop: Optional[asyncio.AbstractEventLoop] = None):
        self.consumer_key = consumer_key
        self.jira_url = jira_url
        self.rsa_private_key = rsa_private_key
        self.rsa_public_key = rsa_public_key
        self.test_jira_issue = test_jira_issue
        self.redirect_url = redirect_url
        self.app = app
        self.auth_response_text = auth_response_text
        self.loop = loop
        self.consumer = None
        self.request_token = None
        self.auth_url = None
        self.access_token = {}
        self._oauth_result_lock: asyncio.Lock = None

    @classmethod
    def from_file(cls) -> 'JiraOAuth':
        self = cls()
        self.read_jira_oauth_init_parameters_from_file()
        return self

    @property
    def data_url(self) -> str:
        return str(
            URL(self.jira_url).with_path(path=f'/rest/api/2/issue/{self.test_jira_issue}').with_query(fields='summary'))

    def read_jira_oauth_init_parameters_from_file(self) -> None:
        config = ConfigParser()
        config.optionxform = str  # Read config file as case insensitive
        config.read(self.starter_oauth_config_file)

        self.consumer_key = config.get("oauth_config", "consumer_key")
        self.jira_url = config.get("oauth_config", "jira_url")
        self.rsa_private_key = self._read_file(path=self.rsa_private_key_file_path)
        self.rsa_public_key = self._read_file(path=self.rsa_public_key_file_path)
        self.test_jira_issue = config.get("oauth_config", "test_jira_issue")

    async def generate_request_token_and_auth_url(self) -> None:
        request_token_url = str(URL(self.jira_url).with_path(path='/plugins/servlet/oauth/request-token'))
        authorize_url = str(URL(self.jira_url).with_path(path='/plugins/servlet/oauth/authorize'))

        self.consumer = oauth2.Consumer(key=self.consumer_key, secret=self.rsa_public_key)
        client = await aioauth2.Client.create(consumer=self.consumer)
        signature_method = JiraOAuth.SignatureMethod_RSA_SHA1(rsa_private_key=self.rsa_private_key)
        await client.set_signature_method(method=signature_method)

        # Step 1: Get a request token. This is a temporary token that is used for
        # having the user authorize an access token and to sign the request to obtain
        # said access token.
        resp, content = await client.request(uri=request_token_url, method="POST")
        if resp['status'] != '200':
            raise Exception(f"Invalid response resp['status']: content")

        # If output is in bytes. Let's convert it into String.
        if type(content) == bytes:
            content = content.decode('UTF-8')

        self.request_token = dict(parse.parse_qsl(content))

        if self.app is not None and self.redirect_url is not None:
            self._oauth_result_lock = asyncio.Lock(loop=self.loop)
            await self._oauth_result_lock.acquire()

        query = dict(oauth_token=self.request_token['oauth_token'])
        if self.redirect_url is not None:
            query.update(oauth_callback=str(self.redirect_url))
        self.auth_url = str(URL(authorize_url).with_query(query))

    async def generate_access_token(self):
        # Step 3: Once the consumer has redirected the user back to the oauth_callback
        # URL you can request the access token the user has approved. You use the
        # request token to sign this request. After this is done you throw away the
        # request token and use the access token returned. You should store this
        # access token somewhere safe, like a database, for future use.
        token = oauth2.Token(key=self.request_token['oauth_token'], secret=self.request_token['oauth_token_secret'])
        # token.set_verifier(oauth_verifier)
        client = await aioauth2.Client.create(consumer=self.consumer, token=token)
        await client.set_signature_method(JiraOAuth.SignatureMethod_RSA_SHA1(rsa_private_key=self.rsa_private_key))

        if self._oauth_result_lock is not None:
            await self._oauth_result_lock.acquire()

        resp, content = await client.request(uri=self._access_token_url, method="POST")
        # Response is coming in bytes. Let's convert it into String.
        # If output is in bytes. Let's convert it into String.
        if type(content) == bytes:
            content = content.decode('UTF-8')
        self.access_token = dict(parse.parse_qsl(qs=content))

    @property
    def _access_token_url(self) -> str:
        return str(URL(self.jira_url).with_path(path='/plugins/servlet/oauth/access-token'))

    @staticmethod
    def _read_file(path: PathOrStr) -> str:
        with open(file=str(path), mode='r') as f:
            return f.read()

    async def process_oauth_result(self, request: Request) -> Response:
        if request.query['oauth_token'] == self.request_token['oauth_token']:
            self._oauth_result_lock.release()
        return Response(text=self.auth_response_text, content_type='text/html')
