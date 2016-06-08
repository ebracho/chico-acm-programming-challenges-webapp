import os
import binascii
import json
from datetime import datetime, timedelta
from functools import partial
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, \
    DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug import generate_password_hash, check_password_hash
from flask import request, abort, jsonify

import api

engine = create_engine('sqlite:///api/riker.db', echo=False)
DBSession = sessionmaker(engine)
Base = declarative_base()


# Models

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    pwhash = Column(String)
    creation_time = Column(DateTime, default=datetime.utcnow)

    def __init__(self, id_, password):
        self.id = id_
        self.pwhash = generate_password_hash(password)

    def __repr__(self):
        return '<User: id={0}, creation_time={1}>'.format(
            self.id, self.creation_time)

    def auth(self, password):
        return check_password_hash(self.pwhash, password)

    def to_dict(self):
        """Return dict representation of data"""
        return {
            'userId': self.id,
            'creationTime': str(self.creationtime)
        }

    @staticmethod
    def by_id(id_):
        db_session = DBSession()
        return db_session.query(User).filter(User.id==id_).first()

    @staticmethod
    def auth_user(id_, password):
        db_session = DBSession()
        user = db_session.query(User).filter(User.id==id_).first()
        return False if not user else user.auth(password)
            

class ApiSession(Base):
    __tablename__ = 'api_sessions'
    user_id = Column(String, ForeignKey('users.id'))
    session_key = Column(LargeBinary, default=partial(os.urandom, 16), primary_key=True)
    expiration = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))

    def __repr__(self):
        return '<ApiSession: user_id={0}, expiration={1}>'.format(
            self.user_id, self.expiration)

    def is_expired(self):
        """Check whether session key has expired"""
        return datetime.utcnow() > self.expiration

    def get_key(self):
        """Return session key formatted as hex string"""
        return binascii.hexlify(self.session_key).decode('utf-8')

    def to_dict(self):
        """Return dict representation of data"""
        return {
            'userId': self.user_id,
            'sessionKey': self.get_key(),
            'expiration': str(self.expiration)
        }

    @staticmethod
    def get_session(key):
        """Return session object with given api session key"""
        key = binascii.unhexlify(key)
        db_session = DBSession()
        api_session = db_session.query(ApiSession).filter(
            ApiSession.session_key==key).first()
        return api_session

    @staticmethod
    def get_user_id(key):
        """Return the user id bound to api session key"""
        api_session = ApiSession.get_session(key)
        return api_session.user_id if api_session else None

    @staticmethod
    def validate_session(key):
        """Check for unexpired session for given user/key."""
        api_session = ApiSession.get_session(key)
        return False if not api_session else not api_session.is_expired()

    @staticmethod
    def end_session(key):
        """Set expiration of valid session to present time"""
        if ApiSession.validate_session(key):
            key = binascii.unhexlify(key)
            db_session = DBSession()
            api_session = db_session.query(ApiSession).filter(
                ApiSession.session_key==key).first()
            api_session.expiration = datetime.utcnow()
            db_session.commit()
            

class Problem(Base):
    __tablename__ = 'problems'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    creation_time = Column(DateTime, default=datetime.utcnow)
    title = Column(String)
    prompt = Column(String)
    test_input = Column(String)
    test_output = Column(String)
    timeout = Column(Integer, default=3)

    def __repr__(self):
        return '<Problem: title="{0}", author={1}>'.format(
        self.title, self.user_id)

    def to_dict(self):
        """Return dict representation of data"""
        return {
            'userId': self.user_id,
            'creationTime': str(self.creation_time),
            'problemId': self.id,
            'prompt': self.prompt,
            'testInput': self.test_input,
            'testOutput': self.test_output,
            'timeout': self.timeout,
        }


class Solution(Base):
    __tablename__ = 'solutions'
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('problems.id'))
    language = Column(String)
    source = Column(String)
    verification = Column(String)
    user_id = Column(String, ForeignKey('users.id'))
    creation_time = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Solution: author={0}>'.format(self.user_id)

    def to_dict(self):
        return {
            'userId': self.user_id,
            'creationTime': str(self.creation_time),
            'solutionId': self.id,
            'problemId': self.problem_id,
            'language': self.language,
            'source': self.source,
            'verification': self.verification,
        }


class ProblemComment(Base):
    __tablename__ = 'problem_comments'
    problem = Column(Integer, ForeignKey('problems.id'))
    body = Column(String)
    user_id = Column(String, ForeignKey('users.id'), primary_key=True)
    creation_time = Column(DateTime, default=datetime.utcnow, primary_key=True)

    def __repr__(self):
        return '<ProblemComment: problem={0}, user={1}, time={2}>'.format(
            self.problem, self.user_id, self.creation_time)

    def to_dict(self):
        return {
            'userId': self.user_id,
            'creationTime': str(self.creation_time),
            'problem': self.problem,
            'body': self.body,
        }


class SolutionComment(Base):
    __tablename__ = 'solution_comments'
    solution = Column(Integer, ForeignKey('solutions.id'))
    body = Column(String)
    user_id = Column(String, ForeignKey('users.id'), primary_key=True)
    creation_time = Column(DateTime, default=datetime.utcnow, primary_key=True)

    def __repr__(self):
        return '<SolutionComment: solution={0}, user={1}, time={2}>'.format(
            self.solution, self.user_id, self.creation_time)

    def to_dict(self):
        return {
            'userId': self.user_id,
            'creationTime': str(self.creation_time),
            'solution': self.solution,
            'body': self.body,
        }

Base.metadata.create_all(engine)


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
    

@api.blueprint.route('/start-session', methods=['POST'])
def start_session():
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

    # Serialize and return session data
    return jsonify(api_session.to_dict())
    

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
        # Parse form arguments
        title = request.form.get('title', None)
        prompt = request.form.get('prompt', None)
        test_input = request.form.get('testInput', '')
        test_output = request.form.get('testOutput', '')
        timeout = request.form.get('timeout', 3)
        if title is None or prompt is None or api_session_key is None:
            raise RequestError('Missing parameter(s).')

        # Validate api session
        api_session_key = request.headers.get('sessionKey', None)
        if not ApiSession.validate_session(api_session_key):
            raise AuthError('Invalid or expired session key.')
        user_id = ApiSession.get_user_id(api_session_key)

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
    if request.method == 'GET':
        # Retrieve resource
        db_session = DBSession()
        problem = db_session.query(Problem).filter(
            Problem.id == problem_id).first()
        if problem is None:
            abort(404)

        # Serialize and return resource
        return jsonify(problem.to_dict())

    else: # request.method == DELETE
        # Validate api session key
        api_session_key = request.headers.get('sessionKey', None)
        if api_session_key is None:
            raise RequestError('Missing parameter(s).')
        if not ApiSession.validate_session(api_session_key):
            raise AuthError('Invalid or expired session key.')

        # Determine whether resource is owned by user
        db_session = DBSession()
        problem = db_session.query(Problem).filter(
            Problem.id == problem_id).first()
        if problem is None:
            abort(404)
        if ApiSession.get_user_id(api_session_key) != problem.user_id:
            raise AuthError('Resource not owned by user.')

        # Delete resource
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
        elif not ApiSession.validate_session(api_session_key):
            raise AuthError('Invalid or expired session key.')

        session.delete(solution)
        session.commit()

        return ''
