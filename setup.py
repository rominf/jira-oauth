# -*- coding: utf-8 -*-
from distutils.core import setup

packages = \
['jira_oauth']

package_data = \
{'': ['*']}

install_requires = \
['PyJWT>=1.7,<2.0',
 'aioauth2>=0.1.0,<0.2.0',
 'aiohttp>=3.4,<4.0',
 'asn1crypto>=0.24.0,<0.25.0',
 'certifi>=2018.11,<2019.0',
 'cffi>=1.11,<2.0',
 'chardet>=3.0,<4.0',
 'click>=7.0,<8.0',
 'cryptography>=2.4,<3.0',
 'dataclasses>=0.6.0,<0.7.0',
 'defusedxml>=0.5.0,<0.6.0',
 'httplib2>=0.12.0,<0.13.0',
 'idna>=2.8,<3.0',
 'oauth2>=1.9,<2.0',
 'oauthlib>=2.1,<3.0',
 'pbr>=5.1,<6.0',
 'poetry-version>=0.1.2,<0.2.0',
 'pycparser>=2.19,<3.0',
 'six>=1.11,<2.0',
 'tlslite>=0.4.9,<0.5.0',
 'urllib3>=1.24,<2.0',
 'yarl>=1.3,<2.0']

entry_points = \
{'console_scripts': ['jira-oauth = jira_oauth.console:main']}

setup_kwargs = {
    'name': 'jira-oauth',
    'version': '0.1.10',
    'description': 'Python library for Jira OAuth ',
    'long_description': "# jira-oauth\n[![License](https://img.shields.io/pypi/l/jira-oauth.svg)](https://www.apache.org/licenses/LICENSE-2.0)\n![PyPI - Python Version](https://img.shields.io/pypi/pyversions/jira-oauth.svg)\n[![PyPI](https://img.shields.io/pypi/v/jira-oauth.svg)](https://pypi.org/project/jira-oauth/)\n\nPython library for Jira OAuth\n\n## RSA private and public key creations\n* Create RSA private key and store it in file **oauth.pem**\n```shell\n$ openssl genrsa -out oauth.pem 1024\n```\n\n* Create RSA public key and store it in file **oauth.pub**\n```\n$ openssl rsa -in oauth.pem -pubout -out oauth.pub\n```\n\n* Share RSA public key **oauth.pub** with your Jira Admin, as they need it during _Jira Application Link_ creation.\n\n## Jira Application Link Creation Steps\n* Login as a Jira administrator\n* Go to **Application links** section under **Application** area\n* Enter dummy url (as oauth token used for API access and not web access) *https://jira-oauth1-rest-api-access*\n* Click on **Create new link** button\n* Click **Continue** on next screen\n* Enter something like **Jira OAuth1 REST API access** as a *Application Name*\n* Check **Create incomindg link** checkbox.\n* Don't need to fill any other information. Click on **Continue**\n* Now you should able to see new Application link with name **Jira OAuth1 REST API access** created and available under section *Configure Application Links* section\n* Click on *pencil* icon to configure **Incoming Authentication**\n  * Enter **jira-oauth1-rest-api-access** (or any other appropriate string) as *Consumer key*\n  * Enter same string **jira-oauth1-rest-api-access** (or any other appropriate string) as *Consumer Name*\n  * Enter content of RSA public key (stored in file **oauth.pub**) as **public key**\n  * Click on **Save**\n\n## Prepare for OAuth Dance\nCreate **starter_oauth.config** in **~/.oauthconfig** folder:\n```ini\n[oauth_config]\njira_url=https://jira.example.com\nconsumer_key=jira-oauth1-rest-api-access\ntest_jira_issue=IDEV-1\n```\n\n## Perform Jira OAuth Dance\n* Python Virtual Environment that we create earlier is active.\n* Run **jira-oauth**.\n* Authenticate in browser as directed below.\n* After successful OAuth generation, you will get another set of values for **oauth_token** and **oauth_token_secret**. These are you tokens that you need to use access Jira without passing credentials.\n```\n$ jira-oauth\nRequest Token: oauth_token=6AOSSREyS9HaACqEcHjcD6RJVms2NjEr, oauth_token_secret=gnpJMfbgUyG8W4dKzFW4PKFbGttV2CWm\n\nGo to the following link in your browser: https://jira.example.com/plugins/servlet/oauth/authorize?oauth_token=6AOSSREyS9HaACqEcHjcD6RJVms2NjEr\nHave you authorized me? (y/n) y\n\nAccess Token: oauth_token=lmOh7LEdvZ2yxKIm5rdQY2ZfZqNdvUV4, oauth_token_secret=gnpJMfbgUyG8W4dKzFW4PKFbGttV2CWm\nYou may now access protected resources using the access tokens above.\n\nAccessing IDEV-1 using generated OAuth tokens:\nSuccess!\nIssue key: IDEV-1, Summary: Internal Devepment Issue #1\n```\n\n## Credits\nThank you, Raju Kadam, for implementing https://github.com/rkadam/jira-oauth-generator\n",
    'author': 'Roman Inflianskas',
    'author_email': 'infroma@gmail.com',
    'url': 'https://github.com/rominf/jira-oauth',
    'packages': packages,
    'package_data': package_data,
    'install_requires': install_requires,
    'entry_points': entry_points,
    'python_requires': '>=3.6,<4.0',
}


setup(**setup_kwargs)
