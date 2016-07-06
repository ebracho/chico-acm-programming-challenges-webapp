from flask import render_template
import frontend

@frontend.blueprint.route('/register')
def problems():
    return render_template('register.html')

