import flask

blueprint = flask.Blueprint('frontend', __name__)

import frontend.views
