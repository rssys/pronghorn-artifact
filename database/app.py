from flask import Flask, request, jsonify
from collections import defaultdict
import json
import logging
from typing import Dict, List

app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)


class CRUD(object):
    def __init__(self) -> None:
        self.store = {}
        self.counter = defaultdict(int)
        logging.info("Initialized CRUD container")

    def _check_id(self, counter: int, next_expected_id: int):
        return next_expected_id < 0 or counter == next_expected_id

    def read(
        self, benchmark: str, next_expected_id: int = -1
    ) -> "tuple[object, bool, int]":
        count = self.counter[benchmark]
        data = self.store.get(benchmark, "")
        logging.info(f"CRUD: Executed read for benchmark: {benchmark}")
        logging.info(f"CRUD (Read): Counter for benchmark {benchmark} is now {count} and next expected id is {next_expected_id}")
        # passed = self._check_id(count, next_expected_id)
        passed = True
        next_expected_id = count  # count should be the same after a read
        return data, passed, next_expected_id

    # If this returns false, the write does NOT go through
    def write(
        self, benchmark: str, data: object, next_expected_id: int = -1
    ) -> "tuple[bool, int]":
        count = self.counter[benchmark]
        if not self._check_id(count, next_expected_id):
            logging.warn(
                f"CRUD: Did not execute write due to id mismatch of actual {count} and expected {next_expected_id}"
            )
            return False, count

        self.counter[benchmark] += 1
        self.store[benchmark] = data

        next_expected_id = count + 1  # count should increase after a write
        logging.info(f"CRUD: Counter for benchmark {benchmark} is now {count} and next expected id is {next_expected_id}")
        logging.info(
            f"CRUD: Executed write of length {len(data)} with next id {next_expected_id}"
        )

        return True, next_expected_id

    def delete(self, benchmark: str) -> "tuple[bool, int]":
        if benchmark not in self.store:
            logging.warn(f"CRUD: Did not execute delete for benchmark: {benchmark}")
            return False, -1

        del self.store[benchmark]
        self.counter[benchmark] = 0

        logging.info(f"CRUD: Executed delete for benchmark: {benchmark}")
        return True, -1


crud: CRUD = CRUD()


@app.route("/read/<benchmark>", methods=["GET"])
def crud_read(benchmark: str):
    next_expected_id = int(request.args.get("next_expected_id"))
    data, passed, next_id = crud.read(benchmark, next_expected_id)
    return jsonify({"data": data, "passed": passed, "next_expected_id": next_id})


@app.route("/write/<benchmark>", methods=["POST"])
def crud_write(benchmark: str):
    next_expected_id = int(request.args.get("next_expected_id"))
    data = request.json
    passed, next_id = crud.write(benchmark, data, next_expected_id)
    return jsonify({"passed": passed, "next_expected_id": next_id})


@app.route("/delete/<benchmark>", methods=["GET"])
def crud_delete(benchmark: str):
    passed, next_id = crud.delete(benchmark)
    return jsonify({"passed": passed, "next_expected_id": next_id})
