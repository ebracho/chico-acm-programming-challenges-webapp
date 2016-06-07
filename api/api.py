import os
from datetime import datetime, timedelta
from functools import partial
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, \
    DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from werkzeug import generate_password_hash, check_password_hash
from flask import request, jsonify

import api

engine = create_engine('sqlite:///api/riker.db')
Session = sessionmaker(engine)
Base = declarative_base()


# Models

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    pwhash = Column(LargeBinary)
    creation_time = Column(DateTime, default=datetime.utcnow)

    def __init__(self, id_, password):
        self.id = id_
        pwhash = generate_password_hash(password)

    def __repr__(self):
        return 'User: id={0}, creation_time={1}'.format(self.id, self.creation_time)

    def auth(self, password):
        return check_password_hash(self.pwhash, password)

    @staticmethod
    def by_id(id_):
        session = Session()
        return session.query(User).filter(User.id==id_).first()

    @staticmethod
    def auth_user(id_, password):
        session = Session()
        user = session.query(User).filter(User.id==id_).first()
        return False if not user else user.auth(password)
            

class ApiSession(Base):
    __tablename__ = 'api_sessions'
    user_id = Column(String, ForeignKey('users.id'))
    key = Column(LargeBinary, default=partial(os.urandom, 16), primary_key=True)
    expiration = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))

    def __repr__(self):
        return 'ApiSession: user_id={0}, expiration={1}'.format(self.user_id, self.expiration)

    def is_expired(self):
        return datetime.utcnow() < self.expiration

    @staticmethod
    def validate_session(user_id, key):
        session = Session()
        apisession = session.query(ApiSession).filter(
            Session.user_id==user_id and Session.key==key).first()
        return False if not apisession else not apisession.is_expired()


class Problem(Base):
    __tablename__ = 'problems'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    creation_time = Column(DateTime, default=datetime.utcnow)
    title = Column(String)
    prompt = Column(String)
    test_input = Column(String)
    test_output = Column(String)

    def __repr__(self):
        return 'Problem: title="{0}", author={1}'.format(self.title, self.user_id)


class Solution(Base):
    __tablename__ = 'solutions'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    creation_time = Column(DateTime, default=datetime.utcnow)
    problem_id = Column(Integer, ForeignKey('problems.id'))
    language = Column(String)
    source = Column(String)
    verification = Column(String)

    def __repr__(self):
        return 'Solution: author={0}'.format(self.user_id)


class ProblemComment(Base):
    __tablename__ = 'problem_comments'
    user_id = Column(String, ForeignKey('users.id'), primary_key=True)
    creation_time = Column(DateTime, default=datetime.utcnow, primary_key=True)
    problem = Column(Integer, ForeignKey('problems.id'))
    body = Column(String)


class SolutionComment(Base):
    __tablename__ = 'solution_comments'
    user_id = Column(String, ForeignKey('users.id'), primary_key=True)
    creation_time = Column(DateTime, default=datetime.utcnow, primary_key=True)
    problem = Column(Integer, ForeignKey('solutions.id'))
    body = Column(String)


Base.metadata.create_all(engine)


# Route Helpers

def camelify(s):
    """Convert snake_case string to camelCase."""
    parts = s.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])

def camelify_object(obj):
    """Recursively camelify keys of obj"""
    if isinstance(obj, dict):
        return { camelify(k):camelify_object(obj[k]) for k in obj }
    elif isinstance(obj, list):
        return [ camelify_object(o) for o in obj ]
    else:
        return obj


# Route exceptions and error handlers

class AuthError(Exception):
    """Exception for authentication failures"""
    pass

class RequestError(Exception):
    """Exception for incorrectly formatted or unfulfillable reqeusts"""
    pass

def build_error_message(msg):
    """Return json error string"""
    return {'errorMsg':msg}

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
        raise RequestError('Missing parameters.')
    if User.by_id(user_id):
        raise RequestError('User {0} already exists.'.format(user_id))
    if not 3 <= len(user_id) <= 15:
        raise RequestError('Invalid user id length.')
    if not 7 <= len(password) <= 128:
        raise RequestError('Invalid password length.')
    session = Session()
    new_user = User(id_=user_id, password=password)
    session.add(new_user)
    session.commit()
    return ''
    

