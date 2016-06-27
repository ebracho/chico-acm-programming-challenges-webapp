import json
from flask import request, abort, jsonify

import api
from api.models import DBSession, User, ApiSession, Problem, Solution, \
ProblemComment, SolutionComment


# Route exceptions and error handlers

class AuthError(Exception):
    """Exception for authentication failures"""
    pass

class RequestError(Exception):
    """Exception for incorrectly formatted or unfulfillable reqeusts"""
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


# Routes

@api.blueprint.route('/')
def doc():
    """Return contents of api.html"""
    with open('api/api.html') as f:
        return f.read()


@api.blueprint.route('/register', methods=['POST'])
def register():
    """Create user or return error message"""
    user_id = request.form['userId']
    password = request.form['password']
    if not (user_id and password):
        raise RequestError('Missing parameter(s).')

    if User.by_id(user_id):
        raise RequestError('User {0} already exists.'.format(user_id))
    if not 3 <= len(user_id) <= 15:
        raise RequestError('Invalid user id length.')
    if not 7 <= len(password) <= 128:
        raise RequestError('Invalid password length.')

    db_session = DBSession()
    new_user = User(user_id, password)
    db_session.add(new_user)
    db_session.commit()
    return ''
    

@api.blueprint.route('/create-session', methods=['POST'])
def create_session():
    """Generate a 30 day api session key"""
    # Parse request args
    user_id = request.form.get('userId', None)
    password = request.form.get('password', None)
    if not (user_id and password):
        raise RequestError('Missing parameter(s).')

    # Validate user credentials
    if not User.auth_user(user_id, password):
        raise AuthError('Incorrect userId/password.')

    # Create api session key
    db_session = DBSession()
    api_session = ApiSession(user_id=user_id)
    db_session.add(api_session)
    db_session.commit()

    # Return serialized data
    return jsonify({
        'userId': api_session.user_id,
        'sessionKey': api_session.get_key(),
        'expiration': api_session.expiration
    })
    

@api.blueprint.route('/end-session', methods=['POST'])
def end_session():
    """Ends the specified session"""
    # Parse request args
    api_session_key = request.headers.get('sessionKey', None)
    if api_session_key is None:
        raise RequestError('Missing parameter(s).')

    # Validate api session
    if not ApiSession.validate_session(api_session_key):
        raise AuthError('Session does not exist.')

    ApiSession.end_session(api_session_key)

    return ''
    

@api.blueprint.route('/problems', methods=['GET','POST'])
def problems():
    """Retrieve or create problem(s)"""
    if request.method == 'GET':
        # Parse query-string arguments
        user_id = request.args.get('userId', None)
        limit = request.args.get('limit', None)

        # Build select query
        db_session = DBSession()
        problems = db_session.query(Problem)
        if user_id is not None:
            problems = problems.filter(Problem.user_id == user_id)
        if limit is not None:
            problems = problems.limit(limit)

        # Serialize and return resource(s)
        return jsonify([problem.to_dict() for problem in problems.all()])
        
    else: # request.method == 'POST'
        # Validate api session
        api_session_key = request.headers.get('sessionKey', None)
        if not ApiSession.validate_session(api_session_key):
            raise AuthError('Invalid or expired session key.')
        user_id = ApiSession.get_user_id(api_session_key)

        # Parse form arguments
        title = request.form.get('title', None)
        prompt = request.form.get('prompt', None)
        test_input = request.form.get('testInput', '')
        test_output = request.form.get('testOutput', '')
        timeout = request.form.get('timeout', 3)
        if title is None or prompt is None: 
            raise RequestError('Missing parameter(s).')

        # Create and write resource
        db_session = DBSession()
        problem = Problem(
            title=title, prompt=prompt, test_input=test_input, 
            test_output=test_output, timeout=timeout, user_id=user_id)
        db_session.add(problem)
        db_session.commit()

        return ''


@api.blueprint.route('/problems/<problem_id>', methods=['GET','DELETE'])
def problem_by_id(problem_id):
    db_session = DBSession()
    problem = db_session.query(Problem).filter(
        Problem.id == problem_id).first()
    if problem is None:
        abort(404)

    if request.method == 'GET':
        return jsonify(problem.to_dict())

    else: # request.method == 'DELETE'
        api_session_key = request.headers.get('sessionKey', None)
        if api_session_key is None:
            raise RequestError('Missing parameter(s).')
        if not ApiSession.validate_session(api_session_key):
            raise AuthError('Invalid or expired session key.')

        if ApiSession.get_user_id(api_session_key) != problem.user_id:
            raise AuthError('Resource not owned by user.')

        db_session.delete(problem)
        db_session.commit()

        return ''


@api.blueprint.route('/solutions', methods=['GET','POST'])
def solutions():
    if request.method == 'GET':
        # Parse request args
        problem_id = request.args.get('problemId', None)
        user_id = request.args.get('userId', None)
        language = request.args.get('language', None)
        verified_only = request.args.get('verifiedOnly', False)
        limit = request.args.get('limit', None)

        # Build select query
        db_session = DBSession()
        solutions = db_session.query(Solution)
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
        
        # Execute query and serialize data
        response_body = jsonify([s.to_dict() for s in solutions.all()])
        return response_body

    else: # request.method == 'POST'
        # Parse request args
        problem_id = request.form.get('problemId', None)
        language = request.form.get('language', None)
        source = request.form.get('source', None)
        if problem_id is None or language is None or source is None:
            raise RequestError('Missing parameter(s)')

        # Validate api session
        api_session_key = request.headers.get('sessionKey', None)
        if api_session_key is None:
            raise AuthError('No session key provided.')
        if not ApiSession.validate_session(api_session_key):
            raise AuthError('Invalid or expired session key.')
        user_id = ApiSession.get_user_id(api_session_key)
        
        # Check whether problem exists
        db_session = DBSession()
        problem = db_session.query(Problem).filter(
            Problem.id == problem_id).first()
        if problem is None:
            raise RequestError('Problem does not exist.')

        # Create solution
        solution = Solution(
            problem_id=problem_id, language=language, source=source, 
            user_id=user_id, verification='pending')
        db_session.add(solution)
        db_session.commit()
        
        # Launch verify thread
        solution.verify()

        return ''
        
        
@api.blueprint.route('/solutions/<solution_id>', methods=['GET','DELETE'])
def solution_by_id(solution_id):
    db_session = DBSession()
    solution = db_session.query(Solution).filter(Solution.id == solution_id)
    if solution is None:
        abort(404)

    if request.method == 'GET':
        return jsonify(solution.to_dict())
    
    else: # request.method == 'DELETE'
        api_session_key = request.headers.get('sessionKey', None)

        if api_session_key is None:
            raise RequestError('No session key provided.')
        if not ApiSession.validate_session(api_session_key):
            raise AuthError('Invalid or expired session key.')
        if ApiSession.get_user_id(api_session_key) != solution.user_id:
            raise AuthError('Resource not owned by user.')

        session.delete(solution)
        session.commit()

        return ''


@api.blueprint.route('/problems/<problem_id>/comments', methods=['GET','POST'])
def problem_comments(problem_id):
    db_session = DBSession()

    if request.method == 'GET':
        comments = db_session.query(ProblemComment).filter(
            ProblemComment.id == problem_id).all()

        response_body = jsonify([c.to_dict() for c in comments])
        return response_body

    else: # request.method == 'POST'

        api_session_key = request.headers.get('sessionKey', None)
        if api_session_key is None:
            raise AuthError('No session key provided.')
        if not ApiSession.validate_session(api_session_key):
            raise AuthError('Invalid or expired session key.')
        
        user_id = ApiSession.get_user_id(api_session_key)
        comment = ProblemComment(
            problem_id=problem_id, user_id=user_id, body=body)

        db_session.add(comment)
        db_session.commit()

        return jsonify(comment.to_dict())


@api.blueprint.route('/problems/comments/<comment_id>', methods=['GET','DELETE'])
def problem_comments_by_id(comment_id):
    db_session = DBSession()
    comment = db_session.query(ProblemComment).filter(
        ProblemComment.id == comment_id).first()
        
    if problem_comment is None:
        abort(404)

    if request.method == 'GET':
        return jsonify(problem_comment.to_dict())
    
    else: # request.method == 'DELETE'
        api_session_key = request.headers.get('sessionKey', None)
        if api_session_key is None:
            raise AuthError('No session key provided.')
        if not ApiSession.validate_session(api_session_key):
            raise AuthError('Invalid or expired session key.')
        if ApiSession.get_user_id(api_session_key) != comment.user_id:
            raise AuthError('Resource not owned by user.')
    
        session.delete(comment)
        session.commit()
    
        return ''


@api.blueprint.route('/solution/<solution_id>/comments', methods=['GET','POST'])
def solution_comments(solution_id):
    db_session = DBSession()

    if request.method == 'GET':
        comments = db_session.query(SolutionComment).filter(
            SolutionComment.id == solution_id)

        response_body = jsonify([c.to_dict() for c in comments.all()])
        return response_body

    else: # request.method == 'POST'

        api_session_key = request.headers.get('sessionKey', None)
        if api_session_key is None:
            raise AuthError('No session key provided.')
        if not ApiSession.validate_session(api_session_key):
            raise AuthError('Invalid or expired session key.')
        
        user_id = ApiSession.get_user_id(api_session_key)
        comment = SolutionComment(
            solution_id=solution_id, user_id=user_id, body=body)

        db_session.add(comment)
        db_session.commit()

        return jsonify(comment.to_dict())


@api.blueprint.route('/solutions/comments/<comment_id>', methods=['GET','DELETE'])
def solution_comments_by_id(comment_id):
    db_session = DBSession()
    comment = db_session.query(SolutionComment).filter(
        SolutionComment.id == comment_id).first()
        
    if problem_comment is None:
        abort(404)

    if request.method == 'GET':
        return jsonify(comment.to_dict())
    
    else: # request.method == 'DELETE'
        api_session_key = request.headers.get('sessionKey', None)
        if api_session_key is None:
            raise AuthError('No session key provided.')
        if not ApiSession.validate_session(api_session_key):
            raise AuthError('Invalid or expired session key.')
        if ApiSession.get_user_id(api_session_key) != problem_comment.user_id:
            raise AuthError('Resource not owned by user.')
    
        session.delete(comment)
        session.commit()
    
        return ''

