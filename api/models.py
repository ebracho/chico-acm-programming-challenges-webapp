import os
import binascii
import json
from datetime import datetime, timedelta
from functools import partial

from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, \
    DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship
from werkzeug import generate_password_hash, check_password_hash


engine = create_engine('sqlite:///api/riker.db', echo=True)
DBSession = scoped_session(sessionmaker(engine))
Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    pwhash = Column(String)
    creation_time = Column(DateTime, default=datetime.utcnow)

    def __init__(self, id_, password):
        self.id = id_
        self.pwhash = generate_password_hash(password)

    def auth(self, password):
        return check_password_hash(self.pwhash, password)


class ApiSession(Base):
    __tablename__ = 'api_sessions'
    user_id = Column(String, ForeignKey('users.id'))
    session_key = Column(
        LargeBinary, default=partial(os.urandom, 16), primary_key=True)
    expiration = Column(
        DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))

    def is_expired(self):
        """Check whether session key has expired"""
        return datetime.utcnow() > self.expiration

    def get_key(self):
        """Return session key formatted as hex string"""
        return binascii.hexlify(self.session_key).decode('utf-8')

    @staticmethod
    def get_user_id(key):
        """Return the user id bound to api session key"""
        api_session = ApiSession.get_session(key)
        return api_session.user_id if api_session else None

    @staticmethod
    def get_session(key):
        """Return session object with given api session key"""
        key = binascii.unhexlify(key)
        db_session = DBSession()
        api_session = db_session.query(ApiSession).filter(
            ApiSession.session_key==key).first()
        return api_session

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


import verify
import eventlet
eventlet.monkey_patch() # Required for eventlet to work with Flask

class Solution(Base):
    __tablename__ = 'solutions'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    creation_time = Column(DateTime, default=datetime.utcnow)
    problem_id = Column(Integer, ForeignKey('problems.id'))
    language = Column(String)
    source = Column(String)
    verification = Column(String) # Status string returned by verify.verify

    problem = relationship('Problem')

    """
    Verifies the correctness of the solution using `verify.verify`.
    Task is launched in a separate thread to avoid stalling the server.
    Verify threads must acquire verify_sem to avoid running too many
    verification jobs at once.
    """
    _verify_sem = eventlet.semaphore.Semaphore(4)
    def verify(self):
        def thread():
            with Solution._verify_sem:
                self.verification = verify.verify(
                    self.language, self.source, self.problem.test_input, 
                    self.problem.test_output, self.problem.timeout)
                session = DBSession()
                session.add(self)
                session.commit()

        eventlet.spawn_n(thread)
        
    
class ProblemComment(Base):
    __tablename__ = 'problem_comments'
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('problems.id'))
    body = Column(String)
    user_id = Column(String, ForeignKey('users.id'))
    creation_time = Column(DateTime, default=datetime.utcnow)


class SolutionComment(Base):
    __tablename__ = 'solution_comments'
    id = Column(Integer, primary_key=True)
    solution_id = Column(Integer, ForeignKey('solutions.id'))
    body = Column(String)
    user_id = Column(String, ForeignKey('users.id'))
    creation_time = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine)

