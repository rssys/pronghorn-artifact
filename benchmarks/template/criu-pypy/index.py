# Copyright (c) Alex Ellis 2017. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for full license information.

from flask import Flask, request
from function import handler
from waitress import serve
import os

app = Flask(__name__)


def is_true(val):
    return len(val) > 0 and val.lower() == "true" or val == "1"


@app.before_request
def fix_transfer_encoding():
    """
    Sets the "wsgi.input_terminated" environment flag, thus enabling
    Werkzeug to pass chunked requests as streams.  The gunicorn server
    should set this, but it's not yet been implemented.
    """

    transfer_encoding = request.headers.get("Transfer-Encoding", None)
    if transfer_encoding == u"chunked":
        request.environ["wsgi.input_terminated"] = True


@app.route("/", defaults={"path": ""}, methods=["POST", "GET"])
def main_route(path):
    raw_body = os.getenv("RAW_BODY", "false")

    as_text = True

    if is_true(raw_body):
        as_text = False

    mutability = float(request.args.get("mutability"))

    ret = handler.handle(mutability)

    with open("requestLog.txt", "a") as fp:
        fp.write(str(ret['server_time']) + "\n")

    return ret

@app.route("/snapshot", defaults={"path": ""}, methods=["POST", "GET"])
def snapshot_route(path):
    raw_body = os.getenv("RAW_BODY", "false")

    as_text = True

    if is_true(raw_body):
        as_text = False

    with open("requestLog.txt", "a") as fp:
        fp.write("-1\n")

    return ('', 200)


@app.route("/_/health", methods=["POST", "GET"])
def noop():
    return ('', 200)


if __name__ == '__main__':
    serve(app, host='0.0.0.0', port=8080)
