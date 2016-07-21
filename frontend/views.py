from flask import render_template, jsonify
import frontend
import verify
import json


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


@frontend.blueprint.route('/problems/<problem_id>')
def problem(problem_id):
    return render_template('problem.html', problem_id=problem_id)


@frontend.blueprint.route('/problems/<problem_id>/submit-solution')
def submit_solution(problem_id):
    return render_template(
        'submitsolution.html', problem_id=problem_id, 
        supported_languages=json.dumps(verify.supported_languages))


@frontend.blueprint.route('/problems/<problem_id>/solutions/<solution_id>')
def solution(problem_id, solution_id):
    return render_template(
        'solution.html', problem_id=problem_id, solution_id=solution_id)
    
