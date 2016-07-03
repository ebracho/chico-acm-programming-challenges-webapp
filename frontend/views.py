from flask import url_for
import frontend

@frontend.blueprint.route('/problems')
def problems():
    return render_template('problems')

