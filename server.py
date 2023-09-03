#!/usr/bin/env python3

from flask import Flask, request

import libroll as lib
from processes import PROCESS_MGR

app = Flask(__name__)


@app.route('/', methods=['POST'])
def receive_post():
    data = request.form
    parameters = dict(data.items())
    args = dict["args"]
    PROCESS_MGR.start("spin rollup", f"python roll.py {args}")
    return "received"


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8000)