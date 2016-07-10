from flask import render_template
import frontend


@frontend.blueprint.route('/')
def home():
    return render_template('home.html')


@frontend.blueprint.route('/register')
def register():
    return render_template('register.html')


@frontend.blueprint.route('/login')
def login():
    return render_template('login.html')

