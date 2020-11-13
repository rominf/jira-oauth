FROM ubuntu:bionic

RUN apt-get update && apt-get install -y --no-install-recommends \
	build-essential \
	python3 \
	python3-dev \
	python3-pip \
	python3-setuptools \
	python3-wheel

RUN pip3 install jira-oauth
COPY .oauthconfig /root/.oauthconfig
WORKDIR /root

EXPOSE 8080
CMD jira-oauth
