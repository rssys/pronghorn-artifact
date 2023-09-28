FROM ubuntu:latest

WORKDIR /home/app
COPY . /home/app/

ENV PATH=$PATH:/home/app/.local/bin

RUN apt-get update

RUN apt-get install -y python3 curl rr

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && python3 get-pip.py && rm get-pip.py

RUN pip install -r requirements.txt

WORKDIR /home/app/function/
RUN pip install --user -r requirements.txt

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

ENV fprocess="python3 index.py"
ENV cgi_headers="true"
ENV upstream_url="http://127.0.0.1:8080"
ENV mode="http"

EXPOSE 8080

HEALTHCHECK --interval=5s CMD [ -e /tmp/.lock ]

CMD ["python3", "index.py"]