# syntax = docker/dockerfile:experimental

FROM firebolt55439/criu:latest as criu

FROM pfelipefeitosa/of-watchdog:criu-light as watchdog

FROM skharban/pypy:alpine-v3.11 as pypy

WORKDIR /home/app
COPY . /home/app/

ENV PATH=$PATH:/home/app/.local/bin

COPY --from=criu /usr/local/sbin/criu /usr/local/sbin/criu
COPY --from=criu /usr/lib/libprotobuf-c.so.1 /usr/lib/libprotobuf-c.so.1
COPY --from=criu /usr/lib/libnl-3.so.200 /usr/lib/libnl-3.so.200
COPY --from=criu /usr/lib/libnet.so.* /usr/lib/
RUN chmod +x /usr/local/sbin/criu

COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

RUN apk add --no-cache jpeg-dev zlib-dev
RUN apk add --no-cache --virtual .build-deps build-base linux-headers 

RUN pypy3 -m pip install -r requirements.txt

COPY warmup.sh .
RUN chmod a+x warmup.sh

WORKDIR /home/app/function/
RUN pypy3 -m pip install --user -r requirements.txt

RUN apk --no-cache add curl python3
RUN apk --no-cache add iptables
RUN python3 -m pip install requests minio

ARG TEST_COMMAND=tox
ARG TEST_ENABLED=true
RUN if [ "$TEST_ENABLED" == "false" ]; then \
    echo "skipping tests";\
    else \
    eval "$TEST_COMMAND"; \
    fi

WORKDIR /home/app/

RUN mkdir resource
COPY function/resource resource/

ENV fprocess="pypy3 index.py"
ENV cgi_headers="true"
ENV upstream_url="http://127.0.0.1:8080"
ENV mode="http"

EXPOSE 8080

HEALTHCHECK --interval=5s CMD [ -e /tmp/.lock ]

COPY function-service/ ./service
# CMD criu restore -d -v3 && tail -f /dev/null
# CMD python3 service/main.py
CMD ./warmup.sh