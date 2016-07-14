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


@frontend.blueprint.route('/submit-problem')
def submit_problem():
    return render_template('submitproblem.html')


@frontend.blueprint.route('/problem/<problem_id>')
def problem(problem_id):
    return render_template('problem.html', problem_id=problem_id)

