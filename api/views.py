import json
import functools
from flask import request, g, abort, jsonify

import api
from api.models import (DBSession, User, ApiSession, Problem, Solution, 
    ProblemComment, SolutionComment)


# Application context functions

def get_db_session():
    """Opens a new database session if there is not one already for the current
    application context."""
    if not hasattr(g, 'db_session'):
        g.db_session = DBSession()
    return g.db_session

def close_db_session():
    if hasattr(g, 'db_session'):
        g.db_session.commit()
        g.db_session.close()
        delattr(g, 'db_session')

@api.blueprint.after_request
def after_request(response):
    close_db_session()
    return response


# Route exceptions and error handlers

class AuthError(Exception):
    """Exception for authentication failures."""
    pass

class RequestError(Exception):
    """Exception for incorrectly formatted or unfulfillable reqeusts."""
    pass

class ResourceNotFound(Exception):
    """Exception for requests for non-existent resource(s)."""
    pass


def build_error_message(msg):
    """Return json error string"""
    return {'errorMsg': msg}

@api.blueprint.errorhandler(AuthError)
def autherror_handler(e):
    return jsonify(build_error_message(str(e))), 401

@api.blueprint.errorhandler(RequestError)
def requesterror_handler(e):
    return jsonify(build_error_message(str(e))), 400

@api.blueprint.errorhandler(ResourceNotFound)
def resourcenotfound_handler(e):
    return jsonify(build_error_message(str(e))), 404


# Route Decorators

def requires_login(view):
    """Decorator for views that require valid user credentials. The view 
    function must accept the kwarg `user_id`."""
    @functools.wraps(view)
    def auth_user_wrapper(*args, **kwds):
        db_session = get_db_session()
        user_id = request.form.get('userId', None)
        password = request.form.get('password', None)
        if user_id is None or password is None:
            raise RequestError('Missing parameter(s).')
        user = db_session.query(User).filter(User.id==user_id).first()
        if user is None:
            raise AuthError('Invalid userId/password.')
        elif not user.auth(password):
            raise AuthError('Invalid userId/password.')
        return view(*args, user_id=user_id, **kwargs)

    return auth_user_wrapper


def requires_api_session(view):
    """Decorator for views that require an api session. The view function
    must accept the kwarg `api_session`."""
    @functools.wraps(view)
    def auth_api_session_wrapper(*args, **kwds):
        db_session = get_db_session()
        api_session_key = request.form.get('sessionKey', None)
        if api_session_key is None:
            raise RequestError('Missing parameter(s).')
        api_session = ApiSession.get_session(db_session, api_session_key)
        if api_session is None:
            raise AuthError('Invalid or expired session key')
        return view(*args, api_session=api_session, **kwds)

    return auth_api_session_wrapper


# Routes

@api.blueprint.route('/')
def root():
    """Serve api doc page"""
    with open('api/api.html') as f:
        return f.read()


@api.blueprint.route('/register', methods=['POST'])
def register():
    """Create new user"""
    # Parse request parameters
    user_id = request.form['userId']
    password = request.form['password']
    if not (user_id and password):
        raise RequestError('Missing parameter(s).')

    # Validate parameters
    if User.exists(user_id):
        raise RequestError('User {0} already exists.'.format(user_id))
    if not 3 <= len(user_id) <= 15:
        raise RequestError('User id must be between 3 and 15 chars.')
    if not 7 <= len(password) <= 128:
        raise RequestError('Password must be between 7 and 128 chars.')

    # Create new user
    db_session = get_db_session()
    new_user = User(user_id, password)
    db_session.add(new_user)

    return ''
    

@api.blueprint.route('/create-session', methods=['POST'])
@requires_login
def create_session(user_id):
    """Generate a 30 day api session key"""
    # Create api session key
    db_session = get_db_session()
    api_session = ApiSession(user_id=user_id)
    db_session.add(api_session)

    # Apply default column values to api_session before serializing
    db_session.commit() 

    # Serialize and return data.
    res = {
        'userId': api_session.user_id,
        'sessionKey': api_session.get_key(),
        'expiration': api_session.expiration
    }
    return jsonify(res)
    

@api.blueprint.route('/end-session', methods=['POST'])
@requires_api_session
def end_session(api_session):
    api_session.expire()
    get_db_session().add(api_session)
    return ''
    

@api.blueprint.route('/problems', methods=['GET'])
def problems():
    user_id = request.args.get('userId', None)
    limit = request.args.get('limit', None)

    # Build select query
    db_session = get_db_session()
    problems = db_session.query(Problem).order_by(Problem.submission_time)
    if user_id is not None:
        problems = problems.filter(Problem.user_id == user_id)
    if limit is not None:
        problems = problems.limit(limit)

    # Serialize and return response body
    res = [{
        'problemId': problem.id,
        'userId': problem.user_id,
        'submissionTime': problem.submission_time,
        'title': problem.title,
        'prompt': problem.prompt
    } for problem in problems.all() ]

    return jsonify(res)


@api.blueprint.route('/problems', methods=['POST'])
@requires_api_session
def create_problem(api_session):
    # Parse form arguments
    title = request.form.get('title', None)
    prompt = request.form.get('prompt', None)
    test_input = request.form.get('testInput', '')
    test_output = request.form.get('testOutput', '')
    timeout = request.form.get('timeout', 3)
    if title is None or prompt is None: 
        raise RequestError('Missing parameter(s).')

    # Create and write resource
    problem = Problem(
        title=title, prompt=prompt, test_input=test_input, 
        test_output=test_output, timeout=timeout, user_id=user_id)
    get_db_session().add(problem)

    # Serialize and return response body
    return jsonify({
        'problemId': problem.id,
        'userId': problem.user_id,
        'submissionTime': problem.submission_time,
        'title': problem.title,
        'prompt': problem.prompt
    })


@api.blueprint.route('/problems/<problem_id>', methods=['GET'])
def problem_by_id(problem_id):
    db_session = get_db_session()

    # Validate problem id
    problem = db_session.query(Problem).filter(
        Problem.id == problem_id).first()
    if problem is None:
        raise ResourceNotFound('Problem does not exist.')
    
    return jsonify({
        'problemId': problem.id,
        'userId': problem.user_id,
        'submissionTime': problem.submission_time,
        'title': problem.title,
        'prompt': problem.prompt
    })


@api.blueprint.route('/problems/<problem_id>', methods=['PUT'])
@requires_api_session
def update_problem(api_session, problem_id):
    """Updates `problem_id`. Parameters not provided will keep 
    their original values"""
    db_session = get_db_session()

    # Parse and validate problem id
    problem = db_session.query(Problem).filter(
        Problem.id == problem_id).first()
    if problem is None:
        raise ResourceNotFound('Problem does not exist.')

    # Verify ownership
    if problem.user_id != api_session.user_id:
        raise AuthError('Resource does not belong to user.')

    # Update problem
    problem.title = request.form.get('title', problem.title)
    problem.prompt = request.form.get('prompt', problem.prompt)
    problem.test_input = request.form.get('testInput', problem.test_input)
    problem.test_output = request.form.get('testOutput', problem.test_output)
    problem.timeout = request.form.get('timeout', problem.timeout)

    return ''
    
    

@api.blueprint.route('/problems/<problem_id>', methods=['DELETE'])
@requires_api_session
def delete_problem(api_session, problem_id):
    db_session = get_db_session()

    # Parse and validate problem id
    problem = db_session.query(Problem).filter(
        Problem.id == problem_id).first()
    if problem is None:
        raise ResourceNotFound('Problem does not exist.')

    # Verify ownership
    if problem.user_id != api_session.user_id:
        raise AuthError('Resource does not belong to user.')

    db_session.delete(problem)
    return ''


@api.blueprint.route('/solutions', methods=['GET'])
def solutions():
    # Parse request args
    problem_id = request.args.get('problemId', None)
    user_id = request.args.get('userId', None)
    language = request.args.get('language', None)
    verified_only = request.args.get('verifiedOnly', False)
    limit = request.args.get('limit', None)

    # Build select query
    solutions = get_db_session().query(Solution).order_by(Solution.submission_time)
    if problem_id:
        solutions = solutions.filter(Solution.problem_id == problem_id)
    if user_id:
        solutions = solutions.filter(Solution.user_id == user_id)
    if language:
        solutions = solutions.filter(Solution.language == language)
    if verified_only: 
        solutions = solutions.filter(Solution.verified_only == verified_only)
    if limit:
        solutions = solutions.limit(limit)
    
    # Serialize and return data
    res = [{
        'solutionId': solution.id,
        'userId': solution.user_id,
        'submissionTime': solusion.submission_time,
        'problemId': solution.problem_id,
        'language': solution.language,
        'source': solution.source,
        'validation': solution.validation
    } for solution in solutions.all() ]
    return jsonify(res)


@api.blueprint.route('/solutions', methods=['POST'])
@requires_api_session
def create_solution(api_session):
    db_session = get_db_session()

    # Parse request args
    problem_id = request.form.get('problemId', None)
    language = request.form.get('language', None)
    source = request.form.get('source', None)
    if problem_id is None or language is None or source is None:
        raise RequestError('Missing parameter(s)')

    # Check whether problem exists
    problem = db_session.query(Problem).filter(
        Problem.id == problem_id).first()
    if problem is None:
        raise RequestError('Problem does not exist.')
    
    # Create solution
    solution = Solution(
        problem_id=problem_id, language=language, source=source, 
        user_id=user_id, verification='pending')
    db_session.add(solution)

    # Spawn solution verification thread
    solution.verify()

    # Serialize and return response body
    return jsonify({
        'solutionId': solution.id,
        'userId': solution.user_id,
        'submissionTime': solusion.submission_time,
        'problemId': solution.problem_id,
        'language': solution.language,
        'source': solution.source,
        'validation': solution.validation
    })


@api.blueprint.route('/solutions/<solution_id>', methods=['GET'])
def solution_by_id(solution_id):
    db_session = get_db_session()

    # Validate solution id
    solution = db_session.query(Solution).filter(
        Solution.id == solution_id).first()
    if solution is None:
        raise ResourceNotFound('Solution does not exist.')
    
    # Serialize and return response body
    return jsonify({
        'solutionId': solution.id,
        'userId': solution.user_id,
        'submissionTime': solusion.submission_time,
        'problemId': solution.problem_id,
        'language': solution.language,
        'source': solution.source,
        'validation': solution.validation
    })


@api.blueprint.route('/solutions/<solution_id>', methods=['PUT'])
@requires_api_session
def update_solution(api_session, solution_id):
    db_session = get_db_session()

    # Validate solution id
    solution = db_session.query(Solution).filter(
        Solution.id == solution_id).first()
    if solution is None:
        raise ResourceNotFound('Solution does not exist.')

    # Verify ownership
    if solution.user_id != api_session.user_id:
        raise AuthError('Resource does not belong to user.')

    # Update solution
    solution.language = request.form.get('language', solution.language)
    source = request.form.get('source', solution.source)
    
    return ''
    

@api.blueprint.route('/solutions/<solution_id>', methods=['DELETE'])
@requires_api_session
def delete_solution(api_session, solution_id):
    db_session = get_db_session

    # Validate solution id
    solution = db_session.query(Solution).filter(
        Solution.id == solution_id).first()
    if solution is None:
        raise ResourceNotFound('Solution does not exist.')

    # Verify ownership
    if solution.user_id != api_session.user_id:
        raise AuthError('Resource does not belong to user.')

    db_session.delete(solution)
    return ''
    

@api.blueprint.route('/problems/<problem_id>/comments', methods=['GET'])
def problem_comments(problem_id):
    db_session = get_db_session()

    # Verify that problem exists
    problem = db_session.query(Problem).filter(
        Problem.problem_id == problem_id).first()
    if problem is None:
        raise ResourceNotFound('Problem does not exist.')

    # Create Query
    comments = (
        db_session.query(ProblemComment)
        .filter(ProblemComment.problem_id == problem_id)
        .order_by(ProblemComment.submission_time)
    )

    # Serialize and return response body
    res = [{
        'problemCommentId': comment.id,
        'userId': comment.user_id,
        'submissionTime': comment.submission_time,
        'problemId': comment.problem_id,
        'body': comment.body
    } for comment in comments.all() ]
    return jsonify(res)
    

@api.blueprint.route('/problems/<problem_id>/comments', methods=['POST'])
@requires_api_session
def create_problem_comment(api_session, problem_id):
    db_session = get_db_session()
    
    # Verify that problem exists
    problem = db_session.query(Problem).filter(
        Problem.problem_id == problem_id).first()
    if problem is None:
        raise ResourceNotFound('Problem does not exist.')

    # Validate form input
    body = reqeust.form.get('Body', None)
    if body is None:
        raise RequestError('Missing parameter(s)')

    # Create comment
    comment = ProblemComment(
        problem_id=problem_id, user_id=api_session.user_id, body=body)
    db_session.add(comment)
    db_session.commit() # Apply default column values to comment

    # Serialize and return response body
    return jsonify({
        'problemCommentId': comment.id,
        'userId': comment.user_id,
        'problemId': comment.problem_id,
        'submissionTime': comment.submission_time,
        'body': comment.body
    })


@api.blueprint.route('/problems/comments/<comment_id>', methods=['GET'])
def problem_comment_by_id(comment_id):
    db_session = get_db_session()

    # Verify that comment exists.
    comment = db_session.query(ProblemComment).filter(
        ProblemComment.id == comment_id).first()
    if comment is None:
        raise ResourceNotFound('Problem comment does not exist.')

    # Serialize and return response body
    return jsonify({
        'problemCommentId': comment.id,
        'userId': comment.user_id,
        'problemId': comment.problem_id,
        'submissionTime': comment.submission_time,
        'body': comment.body
    })


@api.blueprint.route('/problems/comments/<comment_id>', methods=['PUT'])
@requires_api_session
def update_problem_comment(api_session, comment_id):
    db_session = get_db_session()

    # Verify that comment exists.
    comment = db_session.query(ProblemComment).filter(
        ProblemComment.id == comment_id).first()
    if comment is None:
        raise ResourceNotFound('Problem comment does not exist.')

    # Verify resource ownership
    if api_session.user_id != comment.user_id:
        raise AuthError('Resource not does not belong to user.')

    # Update problem comment
    comment.body = request.form.get('body', comment.body)

    return ''

@api.blueprint.route('/problems/comments/<comment_id>', methods=['DELETE'])
@requires_api_session
def delete_problem_comment(api_sesion, comment_id):
    db_session = get_db_session()

    # Verify that comment exists.
    comment = db_session.query(ProblemComment).filter(
        ProblemComment.id == comment_id).first()
    if comment is None:
        raise ResourceNotFound('Problem comment does not exist.')

    # Verify resource ownership
    if api_session.user_id != comment.user_id:
        raise AuthError('Resource not does not belong to user.')

    db_session.delete(comment)
    return ''
    

@api.blueprint.route('/solution/<solution_id>/comments', methods=['GET'])
def solution_comment(solution_id):
    db_session = get_db_session()

    # Verify that solution exists.
    solution = db_session.query(Solution).filter(
        Solution.id == solution_id).first()
    if solution is None:
        raise ResourceNotFound('Solution does not exist.')

    # Create query
    comments = (
        db_session.query(SolutionComment)
        .filter(SolutionComment.id == solution_id)
        .order_by(SolutionComment.submission_time)
    )

    # Serialize and return data
    res = [{
        'solutionCommentId': comment.id,
        'userId': comment.user_id,
        'submissionTime': comment.submission_time,
        'solutionId': comment.solution_id,
        'body': comment.body
    } for comment in comments.all() ]
    return jsonify(res)
    

@api.blueprint.route('/solution/<solution_id>/comments', methods=['POST'])
@requires_api_session
def create_solution_comment(api_session, solution_id):
    db_session = get_db_session()

    # Verify that solution exists.
    solution = db_session.query(Solution).filter(
        Solution.id == solution_id).first()
    if solution is None:
        raise ResourceNotFound('Solution does not exist.')

    # Validate form input
    body = request.form.get('body', None)
    if body is None:
        raise RequestError('Missing parameter(s).')

    # Create solution comment
    solution_comment = SolutionComment(
        solution_id=solution_id, user_id=api_session.user_id, body=body)
    db_session.add(solution_comment)

    return ''


@api.blueprint.route('/solutions/comments/<comment_id>', methods=['GET'])
def solution_comment_by_id(comment_id):
    db_session = get_db_session()

    # Verify existence of comment
    comment = db_session.query(SolutionComment).filter(
        SolutionComment.id == comment_id).first()
    if comment is None:
        raise ResourceNotFound('Solution comment does not exist.')

    # Serialize and return response body
    return jsonify({
        'solutionCommentId': comment.id,
        'userId': comment.user_id,
        'submissionTime': comment.submission_time,
        'solutionId': comment.solution_id,
        'body': comment.body
    })


@api.blueprint.route('/solutions/comments/<comment_id>', methods=['DELETE'])
@requires_api_session
def update_solution_comment(api_session, comment_id):
    db_session = get_db_session()

    # Verify existence of comment
    comment = db_session.query(SolutionComment).filter(
        SolutionComment.id == comment_id).first()
    if comment is None:
        raise ResourceNotFound('Solution comment does not exist.')

    # Verify ownership of comment
    if api_session.user_id != comment.user_id:
        raise AuthError('Resource does not belong to user.')

    # Update solution comment
    comment.body = request.form.get('body', comment.body)

    return ''


@api.blueprint.route('/solutions/comments/<comment_id>', methods=['DELETE'])
@requires_api_session
def delete_solution_comment(api_session, comment_id):
    db_session = get_db_session()

    # Verify existence of comment
    comment = db_session.query(SolutionComment).filter(
        SolutionComment.id == comment_id).first()
    if comment is None:
        raise ResourceNotFound('Solution comment does not exist.')

    # Verify ownership of comment
    if api_session.user_id != comment.user_id:
        raise AuthError('Resource does not belong to user.')

    db_session.delete(comment)
    return ''
    

@api.blueprint.route('/users', methods=['GET'])
def users():
    db_session = get_db_session
    users = db_session.query(User).order_by(User.creation_time)

    res = [{
        'userId': user.id,
        'creationTime': user.creation_time
    } for user in users.all() ]
    return jsonify(res)
    

@api.blueprint.route('/users/<user_id>', methods=['GET'])
def user_by_id(user_id):
    db_session = get_db_session()

    # Lookup user
    user = db_session.query(User).filter(User.id == user_id).first()
    if user is None:
        raise ResourceNotFound('User does not exist.')

    # Build queries to aggregate submissions by user
    problems = (
        db_session.query(Problem)
        .filter(Problem.user_id == user.id)
        .order_by(Problem.submission_time)
    )
    solutions = (
        db_session.query(Solution)
        .filter(Solution.user_id == user.id)
        .order_by(Solution.submission_time)
    )
    problem_comments = (
        db_session.query(ProblemComment)
        .filter(ProblemComment.user_id == user.id)
        .order_by(ProblemComment.submission_time)
    )
    solution_comments = (
        db_session.query(SolutionComment)
        .filter(SolutionComment.user_id == user.id)
        .order_by(SolutionComment.submission_time)
    )
    
    # Get ids of content submitted by user
    problem_ids = [problem.id for problem in problems.all()]
    solution_ids = [solution.id for solution in solutions.all()]
    problem_comment_ids = [comment.id for comment in problem_comments.all()]
    solution_comment_ids = [comment.id for comment in solution_comments.all()]

    # Serialize and return response body
    return jsonify({
        'userId': user.id,
        'creationTime': user.creation_time,
        'problems': problem_ids,
        'solutions': solution_ids,
        'problemComments': problem_comment_ids,
        'solutionComments': solution_comment_ids
    })

