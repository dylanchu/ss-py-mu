FROM python:3.6-alpine
MAINTAINER coderfox<coderfox.fu@gmail.com>
RUN apk update && apk add libsodium git
COPY . /shadowsocks
WORKDIR /shadowsocks/shadowsocks
RUN pip install cymysql
CMD python servers.py
