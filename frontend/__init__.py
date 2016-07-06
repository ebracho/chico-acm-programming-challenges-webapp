import flask

blueprint = flask.Blueprint(
    'frontend', __name__, static_url_path='/static/frontend', 
    static_folder='static', template_folder='templates')

import frontend.views
