#!/usr/bin/env python3.5
from flask import Flask
import api

app = Flask(__name__)
app.register_blueprint(api.blueprint, url_prefix='/api')
app.run(host='0.0.0.0', port=80)

