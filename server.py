#!/usr/bin/env python3
import json
import os

from flask import Flask, request

import libroll as lib
from processes import PROCESS_MGR

app = Flask(__name__)


@app.route('/', methods=['POST'])
def receive_post():
    data = request.form
    parameters = dict(data.items())
    args = parameters["args"]
    deployment_name = parameters["deployment_name"]
    print("args: ", args)
    print("deployment_name: ", deployment_name)
    lib.run("spin rollup", f"python roll.py {args}", forward="self")
    addresses = lib.read_json_file(os.path.join("deployments", deployment_name))
    return json.dumps(addresses)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)