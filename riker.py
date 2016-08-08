from flask import Flask, request, session, render_template, redirect, url_for, g, flash
from models import DBSession, User, Problem, Solution
from verify import supported_languages, verify


app = Flask(__name__)
app.secret_key = 'development_key'


def get_db_session():
    """Opens a new database session if there is not already one for the
    current application context."""
    if not hasattr(g, 'db_session'):
        g.db_session = DBSession()
    return g.db_session


def close_db_session():
    if hasattr(g, 'db_session'):
        g.db_session.commit()
        g.db_session.close()
        delattr(g, 'db_session')


@app.after_request
def after_request(response):
    close_db_session()
    return response


@app.route('/', methods=['GET'])
def home():
    return render_template('home.html')
        

@app.route('/register', methods=['GET'])
def register_form():
    return render_template('register.html')


@app.route('/register', methods=['POST'])
def register():
    db_session = get_db_session()
    user_id = request.form.get('user-id', None)
    password = request.form.get('password', None)
    confirm_password = request.form.get('confirm-password', None)

    def error_response(error_msg):
        return render_template('register.html', error_msg=error_msg)

    if user_id is None or password is None or confirm_password is None:
        return error_response('Missing field(s)')
    if not (3 <= len(user_id) <= 15):
        return error_response('User id must be between 3 and 15 chars')
    if not user_id.isalnum():
        return error_response('User id must be alphanumeric')
    if User.exists(db_session, user_id):
        return error_response('User id already exists')
    if not (7 <= len(password) <= 128):
        return error_response('Password must be between 7 and 128 chars')
    if password != confirm_password:
        return error_response('Passwords do not match')

    user = User(user_id, password)
    db_session.add(user)
    session['logged_in_user'] = user_id
    return redirect(url_for('home'))


@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    db_session = get_db_session()
    user_id = request.form.get('user-id', None)
    password = request.form.get('password', None)
    previous_location = request.form.get('prev', 'home')

    if user_id is None or password is None:
        flash('Missing fields(s)')
        return redirect(url_for('login', prev=previous_location))
    user = db_session.query(User).filter(User.id == user_id).first()
    if user is None:
        flash('Invalid userId/password')
        return redirect(url_for('login', prev=previous_location))
    if not user.auth(password):
        flash('Invalid userId/password')
        return redirect(url_for('login', prev=previous_location))

    session['logged_in_user'] = user_id
    return redirect(url_for(previous_location))
    

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('logged_in_user', None)
    return redirect(url_for('home'))


@app.route('/user/<user_id>', methods=['GET'])
def view_user(user_id):
    return render_template('user.html', user_id=user_id)


@app.route('/problem', methods=['GET'])
def problem_form():
    if 'logged_in_user' not in session:
        flash('Please login first')
        return redirect(url_for('login', prev='problem_form'))
    return render_template('problem-form.html', languages=supported_languages)


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

