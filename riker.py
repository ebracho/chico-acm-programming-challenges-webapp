from flask import Flask, request, session, render_template, redirect, url_for, g, flash
from urllib.parse import urlparse, urljoin
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


def is_safe_url(target):
    """Ensures that target url does not leave this domain"""
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ['http', 'https'] and \
           ref_url.netloc == test_url.netloc


def get_redirect_target(default='/'):
    arg_next = request.args.get('next', None)
    form_next = request.form.get('next', None)
    for target in arg_next, form_next, default:
        if not target:
            continue
        if is_safe_url(target):
            return target
            

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
    next = get_redirect_target()

    if user_id is None or password is None or confirm_password is None:
        flash('Missing field(s)')
    elif not (3 <= len(user_id) <= 15):
        flash('User id must be between 3 and 15 chars')
    elif not user_id.isalnum():
        flash('User id must be alphanumeric')
    elif User.exists(db_session, user_id):
        flash('User id already exists')
    elif not (7 <= len(password) <= 128):
        flash('Password must be between 7 and 128 chars')
    elif password != confirm_password:
        flash('Passwords do not match')
    else:
        user = User(user_id, password)
        db_session.add(user)
        session['logged_in_user'] = user_id
        return redirect(next)

    return render_template('register.html', next=next)


@app.route('/login', methods=['GET'])
def login_form():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    db_session = get_db_session()
    user_id = request.form.get('user-id', None)
    password = request.form.get('password', None)
    next = get_redirect_target()

    if user_id is None or password is None:
        flash('Missing fields(s)')
        return render_template('login.html', next=next)
    user = db_session.query(User).filter(User.id == user_id).first()
    if user is None:
        flash('Invalid userId/password')
        return render_template('login.html', next=next)
    if not user.auth(password):
        flash('Invalid userId/password')
        return render_template('login.html', next=next)

    session['logged_in_user'] = user_id
    return redirect(next)
    

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
        return redirect(url_for('login', next=request.url))
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

