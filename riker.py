from flask import Flask, request, session, render_template
from models import User, Problem, Solution


app = Flask(__name__)
app.secret_key = 'development_key'


@app.route('/register', methods=['GET'])
def register_form():
    pass


@app.route('/register', methods=['POST'])
def register():
    pass


@app.route('/login', methods=['GET'])
def login_form():
    pass


@app.route('/login', methods=['POST'])
def login():
    pass


@app.route('/user/<user_id>', methods=['GET'])
def view_user(user_id):
    pass


@app.route('/problem', methods=['GET'])
def problem_form():
    pass


@app.route('/problem', methods=['POST'])
def create_problem():
    pass


@app.route('/problem/<problem_id>', methods=['GET'])
def view_problem():
    pass


@app.route('/problem/<problem_id>', methods=['DELETE'])
def delete_problem():
    pass


@app.route('/problem/<problem_id>/solution', methods=['GET'])
def solution_form(problem_id):
    pass


@app.route('/problem/<problem_id>/solution', methods=['POST'])
def create_solution(problem_id):
    pass


@app.route('/problem/<problem_id>/solution/<solution_id>', methods=['GET'])
def view_solution(problem_id, solution_id):
    pass


@app.route('/problem/<problem_id>/solution/<solution_id>', methods=['DELETE'])
def delete_solution(problem_id, solution_id):
    pass


app.run(host='0.0.0.0')

