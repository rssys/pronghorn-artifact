# syntax = docker/dockerfile:experimental

FROM firebolt55439/criu:latest as criu

FROM pfelipefeitosa/of-watchdog:criu-light as watchdog

# FROM openjdk:8u212-jdk-alpine as builder
FROM openjdk:17-alpine as builder

RUN apk --no-cache add curl \
    && addgroup -S app && adduser -S -g app app \
    && mkdir -p /opt/ && cd /opt/ \
    && echo "Downloading gradle.." \
    # && curl -sSfL https://services.gradle.org/distributions/gradle-5.5.1-bin.zip -o gradle-bin.zip \
    && curl -sSfL https://services.gradle.org/distributions/gradle-7.2-bin.zip -o gradle-bin.zip \
    && unzip gradle-bin.zip -d /opt/ \
    && rm gradle-bin.zip \
    && apk del curl

# Export some environment variables
# ENV GRADLE_HOME=/opt/gradle-5.5.1/
ENV GRADLE_HOME=/opt/gradle-7.2/
ENV PATH=$PATH:$GRADLE_HOME/bin

RUN mkdir -p /home/app/libs

ENV GRADLE_OPTS="-Dorg.gradle.daemon=false"
WORKDIR /home/app

COPY . /home/app/

RUN gradle build

# FROM openjdk:8u212-jdk-alpine as ship
FROM openjdk:17-alpine as ship

COPY --from=criu /usr/local/sbin/criu /usr/local/sbin/criu
COPY --from=criu /usr/lib/libprotobuf-c.so.1 /usr/lib/libprotobuf-c.so.1
COPY --from=criu /usr/lib/libnl-3.so.200 /usr/lib/libnl-3.so.200
COPY --from=criu /usr/lib/libnet.so.* /usr/lib/
RUN chmod +x /usr/local/sbin/criu

COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog

WORKDIR /home/app
COPY --from=builder /home/app/entrypoint/build/distributions/entrypoint-1.0.zip ./entrypoint-1.0.zip
RUN unzip ./entrypoint-1.0.zip
RUN rm ./entrypoint-1.0.zip

COPY warmup.sh .
RUN chmod +x warmup.sh
RUN apk --no-cache add musl-dev linux-headers g++ openblas-dev
RUN apk --no-cache add curl python3-dev py3-pip # Add py3-pip to install pip3
RUN apk --no-cache add curl python3-dev
RUN apk --no-cache add iptables
RUN pip3 install --upgrade pip
RUN pip3 install requests minio numpy

ENV upstream_url="http://127.0.0.1:8080"
ENV mode="http"
ENV CLASSPATH="/home/app/entrypoint-1.0/lib/*"
ENV WARM_REQ="YES"
ENV HTTP_SERVER_ADDRESS="localhost:8080"
ENV criu_exec="true"
ENV restore_log_path="./restore.log"

ENV fprocess="java -XX:+UnlockExperimentalVMOptions -XX:+UseCGroupMemoryLimitForHeap com.openfaas.entrypoint.App"
EXPOSE 8080

# RUN --security=insecure (setsid java -XX:+UnlockExperimentalVMOptions -XX:+UseCGroupMemoryLimitForHeap com.openfaas.entrypoint.App < /dev/null &> app.log &) && ./warmup.sh && (criu dump -t $(pgrep java) -o dump.log -v3)

HEALTHCHECK --interval=5s CMD [ -e /tmp/.lock ] || exit 1

COPY function-service/ ./service
COPY ./function/resource.txt .
# CMD criu restore -d -v3 && tail -f /dev/null
# CMD python3 service/main.py
CMD ./warmup.sh