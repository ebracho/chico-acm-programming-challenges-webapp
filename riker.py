import os
import binascii
import requests
from urllib.parse import urlencode, parse_qs
from flask import Flask, request, session, render_template, redirect, \
                  url_for, g, flash, abort
from flask_misaka import Misaka
from urllib.parse import urlparse, urljoin
from functools import wraps
from models import DBSession, Problem, Solution, ProblemComment, SolutionComment
from verify import supported_languages, verify



app = Flask(__name__)
Misaka(app) # Load Misaka extension (used for jinja2 markdown filter)
app.secret_key = 'development_key'

app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 # 1 MiB filesize limit
app.config['GITHUB_CLIENT_ID'] = os.environ['GITHUB_CLIENT_ID']
app.config['GITHUB_CLIENT_SECRET'] = os.environ['GITHUB_CLIENT_SECRET']


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


def requires_login(view):
    """Decorator for views that require login. If user is not logged in,
    redirects to github login page then redirects back after login"""
    @wraps(view)
    def decorator(*args, **kwargs):
        if 'logged_in_user' not in session:
            return redirect(url_for('login', redirect_url=request.url))
        return view(*args, **kwargs)
    return decorator



#############################
### Views
#############################

def handle_github_login(session_code):
    data = {
        'client_id': app.config['GITHUB_CLIENT_ID'],
        'client_secret': app.config['GITHUB_CLIENT_SECRET'],
        'code': session_code,
        'state': session.get('state', '')
    }
    result = requests.post(
        'https://github.com/login/oauth/access_token', data=data)
    qs = parse_qs(result.text)
    access_token = qs['access_token']
    result = requests.get(
            'https://api.github.com/user', 
            params={'access_token': access_token})
    session['logged_in_user'] = result.json()['login']
    return redirect(session.pop('redirect_url', url_for('home')))


@app.route('/', methods=['GET'])
def home():
    # Handle github login request
    if 'code' in request.args:
        return handle_github_login(request.args['code'])

    db_session = get_db_session()
    problems = db_session.query(Problem).all()
    return render_template('home.html', problems=problems)


@app.route('/login', methods=['GET'])
def login():
    state = binascii.hexlify(os.urandom(32)).decode('utf-8')
    session['redirect_url'] = request.args.get('redirect_url', url_for('home'))
    session['state'] = state
    query = {
        'client_id': app.config['GITHUB_CLIENT_ID'],
        'state': state
    }
    return redirect(
        'https://github.com/login/oauth/authorize/?' + urlencode(query))
        

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
    return render_template('problem-form.html', validation={}, form_cache={}, preview=False)


@app.route('/problem', methods=['POST'])
def create_problem():
    db_session = get_db_session()
    title = request.form.get('title', '').strip()
    prompt = request.form.get('prompt', '').strip()
    test_input_file = request.files.get('test-input-file', None)
    test_output_file = request.files.get('test-output-file', None)
    timeout = int(request.form.get('timeout', 3))

    form_cache = { 
        'title': title, 
        'prompt': prompt, 
        'timeout': timeout 
    }

    validation = {}
    if not 'logged_in_user' in session:
        abort(401)
    if not title:
        validation['title'] = { 'level': 'error', 'msg': 'Field Required'}
    if not prompt:
        validation['prompt'] = { 'level': 'error', 'msg': 'Field required' }
    if not test_input_file:
        validation['test_input_file'] = { 'level': 'error', 'msg': 'Field required' }
    if not test_output_file:
        validation['test_output_file'] = { 'level': 'error', 'msg': 'Field required' }
    if not 3 <= timeout <= 10:
        abort(400)

    if 'preview' in request.form:
        return render_template(
            'problem-form.html', form_cache=form_cache, preview=True)

    if validation:
        return render_template(
            'problem-form.html', validation=validation, form_cache=form_cache)

    problem = Problem(
        title=title, prompt=prompt, 
        test_input=test_input_file.read().decode('utf-8')[:-1], # remove trailing newline
        test_output=test_output_file.read().decode('utf-8')[:-1], # remove trailing newline 
        timeout=timeout, user_id=session['logged_in_user'])
    db_session.add(problem)
    db_session.commit()

    return redirect(url_for('view_problem', problem_id=problem.id))
    


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
        .filter(Solution.verification=='PASS')
        .order_by(Solution.submission_time)
        .all()
    )
    comments = (
        db_session.query(ProblemComment)
        .filter(ProblemComment.problem_id==problem_id)
        .order_by(ProblemComment.submission_time)
        .all()
    )
    return render_template(
        'view-problem.html', problem=problem, solutions=solutions, 
        comments=comments)


@app.route('/problem/<problem_id>', methods=['POST']) # html forms don't support delete
@requires_login
def delete_problem(problem_id):
    """Deletes problem and all associated comments/solutions form database"""
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
        'solution-form.html', problem=problem, validation={}, form_cache={},
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

    validation = {}
    if source_file is None or source_file.filename == '':
        validation['source_file'] = { 'level': 'error', 'msg': 'Field required' }
    if language is None:
        validation['language'] = { 'level': 'error', 'msg': 'Field required' }
    elif language not in supported_languages:
        validation['language'] = { 'level': 'error', 'msg': 'Language not supported' }

    if validation:
        form_cache = { 'language': language }
        return render_template(
            'solution-form.html', problem=problem, validation=validation, 
            form_cache=form_cache, supported_languages=supported_languages)

    solution = Solution(
        problem_id=problem_id, user_id=session['logged_in_user'], 
        language=language, source=source_file.read().decode('utf-8'), 
        verification='PENDING')
    db_session.add(solution)
    db_session.commit()
    solution.verify() # Launch verification thread

    return redirect(url_for(
        'view_solution', problem_id=problem_id, solution_id=solution.id))

    


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
    body = request.form.get('body', '').strip()

    validation={}
    if not Problem.exists(db_session, problem_id):
        abort(404)
    if not body:
        validation['body'] = { 'level': 'error', 'msg': 'Comment body cannot be empty' }

    if 'preview' in request.form:
        session['form_cache'] = { 'body': body }
        return redirect(url_for(
            'view_problem', problem_id=problem_id, _anchor="comment-form", preview=True))

    if validation:
        session['validation'] = validation
        return redirect(url_for(
            'view_problem', problem_id=problem_id, _anchor="comment-form"))

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
    body = request.form.get('body', '').strip()

    validation={}
    if not Problem.exists(db_session, problem_id):
        abort(404)
    if not Solution.exists(db_session, solution_id):
        abort(404)
    if not body:
        validation['body'] = { 'level': 'error', 'msg': 'Comment body cannot be empty' }

    if 'preview' in request.form:
        session['form_cache'] = { 'body': body }
        return redirect(url_for(
            'view_solution', problem_id=problem_id, solution_id=solution_id,
            _anchor="comment-form", preview=True))

    if validation:
        session['validation'] = validation
        return redirect(url_for(
            'view_solution', problem_id=problem_id, solution_id=solution_id, 
            _anchor="comment-form"))

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



from eventlet import wsgi
import eventlet

if __name__ == '__main__':
    wsgi.server(eventlet.listen(('127.0.0.1', 8091)), app)

