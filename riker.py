from flask import Flask, request, session, render_template, redirect, \
                  url_for, g, flash, abort
from urllib.parse import urlparse, urljoin
from functools import wraps
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
            

def requires_login(view):
    """Decorator for views that require login. If user is not logged in,
    redirects to login page then redirects back after login"""
    @wraps(view)
    def decorator(*args, **kwargs):
        if 'logged_in_user' not in session:
            flash('Please login first')
            return redirect(url_for('login', next=request.url))
        return view(*args, **kwargs)
    return decorator


@app.route('/', methods=['GET'])
def home():
    db_session = get_db_session()
    problems = db_session.query(Problem).all()
    return render_template('home.html', problems=problems)
        

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
    db_session = get_db_session()
    problems = db_session.query(Problem).filter(Problem.user_id==user_id).all()
    return render_template('user.html', user_id=user_id, problems=problems)


@app.route('/problem', methods=['GET'])
@requires_login
def problem_form():
    return render_template('problem-form.html')


@app.route('/problem', methods=['POST'])
def create_problem():
    db_session = get_db_session()
    title = request.form.get('title', None)
    prompt = request.form.get('prompt', None)
    test_input = request.form.get('test-input', '')
    test_output = request.form.get('test-output', '')
    timeout = int(request.form.get('timeout', 3))

    if title is None or prompt is None:
        flash('Missing parameter(s)')
    elif not 3 <= timeout <= 10:
        flash('Timeout must be between 3 and 10 seconds')
    else:
        problem = Problem(
            title=title, prompt=prompt, test_input=test_input,
            test_output=test_output, timeout=timeout, 
            user_id=session['logged_in_user'])
        db_session.add(problem)
        db_session.commit()
        return redirect(url_for('view_problem', problem_id=problem.id))
    
    return render_template('problem-form.html')


@app.route('/problem/<problem_id>', methods=['GET'])
def view_problem(problem_id):
    db_session = get_db_session()
    problem = db_session.query(Problem).filter(Problem.id==problem_id).first()
    if problem is None:
        abort(404)
    return render_template('view-problem.html', problem=problem)


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

