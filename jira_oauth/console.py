#!/usr/bin/env python
import asyncio
import json

import aioauth2
import oauth2

from jira_oauth import JiraOAuth


class JiraOAuthConsole:
    def __init__(self, jira_oauth: JiraOAuth):
        self.jira_oauth = jira_oauth

    def print_url_and_ask_for_continue(self) -> None:
        # Step 2: Redirect to the provider. Since this is a CLI script we do not
        # redirect. In a web application you would redirect the user to the URL
        # below.
        print(f"Go to the following link in your browser: {self.jira_oauth.url}")
        # After the user has granted access to you, the consumer, the provider will
        # redirect you to whatever URL you have told them to redirect to. You can
        # usually define this in the oauth_callback argument as well.
        accepted = 'n'
        while accepted.lower() == 'n':
            accepted = input('Have you authorized me? (y/n) ')

    async def check_access_token(self) -> None:
        print(f"Accessing {self.jira_oauth.test_jira_issue} using generated OAuth tokens:")

        # Now lets try to access the same issue again with the access token. We should get a 200!
        token = oauth2.Token(key=self.jira_oauth.access_token['oauth_token'],
                             secret=self.jira_oauth.access_token['oauth_token_secret'])
        client = await aioauth2.Client.create(consumer=self.jira_oauth.consumer, token=token)
        signature_method = JiraOAuth.SignatureMethod_RSA_SHA1(rsa_private_key=self.jira_oauth.rsa_private_key)
        await client.set_signature_method(method=signature_method)

        resp, content = await client.request(uri=self.jira_oauth.data_url, method="GET")
        if resp['status'] != '200':
            raise Exception("Should have access!")

        print("Success!")
        # If output is in bytes. Let's convert it into String.
        if type(content) == bytes:
            content = content.decode('UTF-8')
        json_content = json.loads(s=content)
        print(f'Issue key: {json_content["key"]}, Summary: {json_content["fields"]["summary"]} ')


async def main():
    jira_oauth = JiraOAuth.from_file()
    await jira_oauth.generate_request_token_and_auth_url()
    jira_oauth_console = JiraOAuthConsole(jira_oauth=jira_oauth)
    print(f"Request Token: oauth_token={jira_oauth.request_token['oauth_token']}, "
          f"oauth_token_secret={jira_oauth.request_token['oauth_token_secret']}")
    print()
    access_token = {'oauth_problem': True}
    while 'oauth_problem' in access_token:
        jira_oauth_console.print_url_and_ask_for_continue()
        await jira_oauth.generate_access_token()
        access_token = jira_oauth.access_token
    print()
    print(f"Access Token: oauth_token={jira_oauth.access_token['oauth_token']}, "
          f"oauth_token_secret={jira_oauth.access_token['oauth_token_secret']}")
    print("You may now access protected resources using the access tokens above.")
    print()
    await jira_oauth_console.check_access_token()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(future=main())
