from flask import Flask, request, session, render_template, redirect, \
                  url_for, g, flash, abort
from flask_misaka import Misaka
from urllib.parse import urlparse, urljoin
from functools import wraps
from models import DBSession, User, Problem, Solution, ProblemComment, SolutionComment
from verify import supported_languages, verify



app = Flask(__name__)
Misaka(app) # Load Misaka extension (used for jinja2 markdown filter)
app.secret_key = 'development_key'



#############################
### View Helper Functions
#############################

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
    """Attempts to find redirect target in request."""
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



#############################
### Views
#############################

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
    problems = (
        db_session.query(Problem)
        .filter(Problem.user_id==user_id)
        .all()
    )
    solutions = (
        db_session.query(Solution)
        .filter(Solution.user_id==user_id)
        .all()
    )
    return render_template(
        'user.html', user_id=user_id, problems=problems, solutions=solutions)


@app.route('/problem', methods=['GET'])
@requires_login
def problem_form():
    return render_template('problem-form.html')


@app.route('/problem', methods=['POST'])
def create_problem():
    db_session = get_db_session()
    title = request.form.get('title', None)
    prompt = request.form.get('prompt', None)
    test_input_file = request.files.get('test-input-file', None)
    test_output_file = request.files.get('test-output-file', None)
    timeout = int(request.form.get('timeout', 3))

    print(request.files)

    if not 'logged_in_user' in session:
        abort(401)
    elif None in [title, prompt, test_input_file, test_output_file]:
        print(title, prompt, test_input_file, test_output_file)
        flash('Missing parameter(s)')
    elif not 3 <= timeout <= 10:
        flash('Timeout must be between 3 and 10 seconds')
    else:
        problem = Problem(
            title=title, prompt=prompt, 
            test_input=test_input_file.read().decode('utf-8'),
            test_output=test_output_file.read().decode('utf-8'), 
            timeout=timeout, user_id=session['logged_in_user'])
        db_session.add(problem)
        db_session.commit()
        return redirect(url_for('view_problem', problem_id=problem.id))
    
    return render_template('problem-form.html')


@app.route('/problem/<problem_id>', methods=['GET'])
def view_problem(problem_id):
    db_session = get_db_session()
    problem = (
        db_session.query(Problem)
        .filter(Problem.id==problem_id)
        .first()
    )
    if problem is None:
        abort(404)
    solutions = (
        db_session.query(Solution)
        .filter(Solution.problem_id==problem_id)
        .order_by(Solution.submission_time)
        .all()
    )
    comments = (
        db_session.query(ProblemComment)
        .filter(ProblemComment.problem_id==problem_id)
        .order_by(ProblemComment.submission_time)
        .all()
    )
    return render_template('view-problem.html', problem=problem, solutions=solutions, comments=comments)


@app.route('/problem/<problem_id>', methods=['POST']) # html forms don't support delete
@requires_login
def delete_problem(problem_id):
    """Deletes problem and all associated solutions form database"""
    db_session = get_db_session()
    problem = (
        db_session.query(Problem)
        .filter(Problem.id == problem_id)
        .first()
    )
    if problem is None:
        abort(404)
    elif problem.user_id != session['logged_in_user']:
        abort(401)
    solutions = (
        db_session.query(Solution)
        .filter(Solution.problem_id == problem_id)
        .all()
    )
    db_session.delete(problem)
    for solution in solutions:
        db_session.delete(solution)
    return redirect(url_for('home'))


@app.route('/problem/<problem_id>/solution', methods=['GET'])
@requires_login
def solution_form(problem_id):
    db_session = get_db_session()
    problem = (
        db_session.query(Problem)
        .filter(Problem.id==problem_id)
        .first()
    )
    if problem is None:
        abort(404)
    return render_template(
        'solution-form.html', problem=problem, 
        supported_languages=supported_languages)


@app.route('/problem/<problem_id>/solution', methods=['POST'])
@requires_login
def create_solution(problem_id):
    db_session = get_db_session()
    problem = (
        db_session.query(Problem)
        .filter(Problem.id==problem_id)
        .first()
    )
    if problem is None:
        abort(404)
    
    source_file = request.files.get('source-file', None)
    language = request.form.get('language', None)
    if source_file is None or language is None:
        flash('Missing parameter(s)')
    elif language not in supported_languages:
        flash('Language not supported')
    else:
        solution = Solution(
            problem_id=problem_id, user_id=session['logged_in_user'], 
            language=language, source=source_file.read().decode('utf-8'), 
            verification='pending')
        db_session.add(solution)
        db_session.commit()
        return redirect(url_for(
            'view_solution', problem_id=problem_id, solution_id=solution.id))

    return redirect(url_for('solution_form', problem_id=problem_id))
    


@app.route('/problem/<problem_id>/solution/<solution_id>', methods=['GET'])
def view_solution(problem_id, solution_id):
    db_session = get_db_session()
    solution = (
        db_session.query(Solution)
        .filter(Solution.id==solution_id)
        .first()
    )
    if solution is None:
        abort(404)
    comments = (
        db_session.query(SolutionComment)
        .filter(SolutionComment.solution_id==solution_id)
        .order_by(SolutionComment.submission_time)
        .all()
    )
    return render_template(
        'view-solution.html', problem=solution.problem, solution=solution, 
        comments=comments)


@app.route('/problem/<problem_id>/solution/<solution_id>', methods=['POST']) # html forms don't support delete
@requires_login
def delete_solution(problem_id, solution_id):
    db_session = get_db_session()
    solution = (
        db_session.query(Solution)
        .filter(Solution.id == solution_id)
        .first()
    )
    if solution is None:
        abort(404)
    elif solution.user_id != session['logged_in_user']:
        abort(401)
    db_session.delete(solution)
    return redirect(url_for('home'))


@app.route('/problem/<problem_id>/comment', methods=['POST'])
@requires_login
def create_problem_comment(problem_id):
    db_session = get_db_session()
    body = request.form.get('body', None)

    if not Problem.exists(db_session, problem_id):
        abort(404)
    elif body is None:
        abort(400)
    elif body == '':
        flash('Comment body cannot be empty')
    else:
        comment = ProblemComment(
            problem_id=problem_id, user_id=session['logged_in_user'], body=body)
        db_session.add(comment)

    return redirect(url_for('view_problem', problem_id=problem_id))
    

@app.route('/problem-comment/<comment_id>/', methods=['POST']) # html forms don't support delete
@requires_login
def delete_problem_comment(comment_id):
    db_session = get_db_session()
    comment = (
        db_session.query(ProblemComment)
        .filter(ProblemComment.id == comment_id)
        .first()
    )
    if comment is None:
        abort(404)
    if comment.user_id != session['logged_in_user']:
        abort(401)

    problem_id = comment.problem_id
    db_session.delete(comment)
    return redirect(url_for('view_problem', problem_id=problem_id))


@app.route('/problem/<problem_id>/solution/<solution_id>/comment', methods=['POST'])
@requires_login
def create_solution_comment(problem_id, solution_id):
    db_session = get_db_session()
    body = request.form.get('body', None)

    if not Problem.exists(db_session, problem_id):
        abort(404)
    elif not Solution.exists(db_session, solution_id):
        abort(404)
    elif body is None:
        abort(400)
    elif body == '':
        flash('Comment body cannot be empty')
    else:
        comment = SolutionComment(
            solution_id=solution_id, user_id=session['logged_in_user'], body=body)
        db_session.add(comment)

    return redirect(url_for(
        'view_solution', problem_id=problem_id, solution_id=solution_id))
    

@app.route('/solution-comment/<comment_id>/delete', methods=['POST']) # html form don't support DELETE
@requires_login
def delete_solution_comment(comment_id):
    db_session = get_db_session()
    comment = (
        db_session.query(SolutionComment)
        .filter(SolutionComment.id == comment_id)
        .first()
    )
    if comment is None:
        abort(404)
    if comment.user_id != session['logged_in_user']:
        abort(401)

    solution_id = comment.solution_id
    problem_id = (
        db_session.query(Solution)
        .filter(Solution.id==solution_id)
        .first()
        .problem_id
    )
    db_session.delete(comment)
    return redirect(url_for(
        'view_solution', problem_id=problem_id, solution_id=solution_id))



#############################
### Jinja2 Template Filters
#############################

@app.template_filter('datetime')
def format_datetime(value):
    return value.strftime('%a %b %d %Y')



app.run(host='0.0.0.0')

