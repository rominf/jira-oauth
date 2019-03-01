# jira-oauth
[![License](https://img.shields.io/pypi/l/jira-oauth.svg)](https://www.apache.org/licenses/LICENSE-2.0)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/jira-oauth.svg)
[![PyPI](https://img.shields.io/pypi/v/jira-oauth.svg)](https://pypi.org/project/jira-oauth/)

Python library for Jira OAuth

## RSA private and public key creations
* Create RSA private key and store it in file **oauth.pem**
```shell
$ openssl genrsa -out oauth.pem 1024
```

* Create RSA public key and store it in file **oauth.pub**
```
$ openssl rsa -in oauth.pem -pubout -out oauth.pub
```

* Share RSA public key **oauth.pub** with your Jira Admin, as they need it during _Jira Application Link_ creation.

## Jira Application Link Creation Steps
* Login as a Jira administrator
* Go to **Application links** section under **Application** area
* Enter dummy url (as oauth token used for API access and not web access) *https://jira-oauth1-rest-api-access*
* Click on **Create new link** button
* Click **Continue** on next screen
* Enter something like **Jira OAuth1 REST API access** as a *Application Name*
* Check **Create incomindg link** checkbox.
* Don't need to fill any other information. Click on **Continue**
* Now you should able to see new Application link with name **Jira OAuth1 REST API access** created and available under section *Configure Application Links* section
* Click on *pencil* icon to configure **Incoming Authentication**
  * Enter **jira-oauth1-rest-api-access** (or any other appropriate string) as *Consumer key*
  * Enter same string **jira-oauth1-rest-api-access** (or any other appropriate string) as *Consumer Name*
  * Enter content of RSA public key (stored in file **oauth.pub**) as **public key**
  * Click on **Save**

## Prepare for OAuth Dance
Create **starter_oauth.config** in **~/.oauthconfig** folder:
```ini
[oauth_config]
jira_url=https://jira.example.com
consumer_key=jira-oauth1-rest-api-access
test_jira_issue=IDEV-1
```

## Perform Jira OAuth Dance
* Python Virtual Environment that we create earlier is active.
* Run **jira-oauth**.
* Authenticate in browser as directed below.
* After successful OAuth generation, you will get another set of values for **oauth_token** and **oauth_token_secret**. These are you tokens that you need to use access Jira without passing credentials.
```
$ jira-oauth
Request Token: oauth_token=6AOSSREyS9HaACqEcHjcD6RJVms2NjEr, oauth_token_secret=gnpJMfbgUyG8W4dKzFW4PKFbGttV2CWm

Go to the following link in your browser: https://jira.example.com/plugins/servlet/oauth/authorize?oauth_token=6AOSSREyS9HaACqEcHjcD6RJVms2NjEr
Have you authorized me? (y/n) y

Access Token: oauth_token=lmOh7LEdvZ2yxKIm5rdQY2ZfZqNdvUV4, oauth_token_secret=gnpJMfbgUyG8W4dKzFW4PKFbGttV2CWm
You may now access protected resources using the access tokens above.

Accessing IDEV-1 using generated OAuth tokens:
Success!
Issue key: IDEV-1, Summary: Internal Devepment Issue #1
```

## Run with Docker

    cp -R ~/.oauthconfig ./
    docker build -t jira-oauth .
    docker run -p 8080:8080 -it --rm jira-oauth


## Credits
Thank you, Raju Kadam, for implementing https://github.com/rkadam/jira-oauth-generator
