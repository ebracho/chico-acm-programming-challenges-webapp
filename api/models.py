import os
import functools
import binascii
import werkzeug
import contextlib
import verify
import eventlet
from datetime import datetime, timedelta

from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, \
    DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, relationship


engine = create_engine('sqlite:///api/riker.db')
DBSession = scoped_session(sessionmaker(engine))
Base = declarative_base()

@contextlib.contextmanager
def scoped_db_session():
    """Provides a transactional scope around a series of operations"""
    session = DBSession()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    pwhash = Column(String)
    creation_time = Column(DateTime, default=datetime.utcnow)

    def __init__(self, id_, password):
        self.id = id_
        self.pwhash = werkzeug.generate_password_hash(password)

    def auth(self, password):
        """Validates password for this user"""
        return werkzeug.check_password_hash(self.pwhash, password)

    @staticmethod
    def exists(db_session, user_id):
        """Returns True if user_id exists."""
        user = db_session.query(User).filter(User.id==user_id).first()
        return user is not None


class ApiSession(Base):
    __tablename__ = 'api_sessions'
    user_id = Column(String, ForeignKey('users.id'))
    session_key = Column(
        LargeBinary, default=functools.partial(os.urandom, 16), primary_key=True)
    expiration = Column(
        DateTime, default=lambda: datetime.utcnow() + timedelta(days=30))

    def get_key(self):
        """Return session key formatted as hex string"""
        return binascii.hexlify(self.session_key).decode('utf-8')

    def is_expired(self):
        """Check whether session key has expired"""
        return datetime.utcnow() > self.expiration

    def expire(self):
        """Expires session if not already expired. Does not commit changes."""
        if not self.is_expired():
            self.expiration = datetime.utcnow()

    @staticmethod
    def get_session(db_session, key):
        """Return session object with given api session key or None"""
        key = binascii.unhexlify(key)
        api_session = db_session.query(ApiSession).filter(
            ApiSession.session_key==key).first()
        return api_session

    @staticmethod
    def get_user_id(db_session, key):
        """Return the user id bound to api session key or None"""
        api_session = ApiSession.get_session(db_session, key)
        return api_session.user_id if api_session else None

    @staticmethod
    def validate_session(db_session, key):
        """Check for unexpired session for given user/key."""
        api_session = ApiSession.get_session(db_session, key)
        return False if api_session is None else not api_session.is_expired()

    @staticmethod
    def end_session(db_session, key):
        """Set expiration of valid session to present time"""
        if ApiSession.validate_session(db_session, key):
            key = binascii.unhexlify(key)
            api_session = db_session.query(ApiSession).filter(
                ApiSession.session_key==key).first()
            api_session.expiration = datetime.utcnow()
            

class Problem(Base):
    __tablename__ = 'problems'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    submission_time = Column(DateTime, default=datetime.utcnow)
    title = Column(String)
    prompt = Column(String)
    test_input = Column(String)
    test_output = Column(String)
    timeout = Column(Integer, default=3)

    @staticmethod
    def exists(db_session, problem_id):
        """Return True if problem_id exists"""
        problem = db_session.query(Problem).filter(Problem.id==problem_id).first()
        return problem is not None
        

eventlet.monkey_patch() # Required for eventlet to work with Flask
class Solution(Base):
    __tablename__ = 'solutions'
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'))
    submission_time = Column(DateTime, default=datetime.utcnow)
    problem_id = Column(Integer, ForeignKey('problems.id'))
    language = Column(String)
    source = Column(String)
    verification = Column(String) # Status string returned by verify.verify

    problem = relationship('Problem')

    _verify_sem = eventlet.semaphore.Semaphore(4)
    @staticmethod
    def verify(solution_id):
        """Verifies the correctness of the solution using `verify.verify`.
        Task is launched in a separate thread to avoid stalling the server.
        Verify threads must acquire verify_sem to avoid running too many
        verification jobs at once."""
        def thread():
            db_session = DBSession()
            solution = db_session.query(Solution).filter(
                Solution.id == solution_id).first()

            print(solution.problem.timeout)

            with Solution._verify_sem:
                solution.verification = verify.verify(
                    solution.language, solution.source, solution.problem.test_input, 
                    solution.problem.test_output, solution.problem.timeout)

            db_session.add(solution)
            db_session.commit()
            db_session.close()

        eventlet.spawn_n(thread)

    @staticmethod
    def exists(db_session, solution_id):
        """Returns True if solution_id exists"""
        solution = db_session.query(Solution).filter(Solution.id==solution_id).first()
        return solution is not None
        
    
class ProblemComment(Base):
    __tablename__ = 'problem_comments'
    id = Column(Integer, primary_key=True)
    problem_id = Column(Integer, ForeignKey('problems.id'))
    body = Column(String)
    user_id = Column(String, ForeignKey('users.id'))
    submission_time = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def exists(db_session, problem_comment_id):
        """Returns True if problem_comment_id exists"""
        problem_comment = db_session.query(ProblemComment).filter(
            ProblemComment.id==problem_comment_id).first()
        return problem_comment is not None

class SolutionComment(Base):
    __tablename__ = 'solution_comments'
    id = Column(Integer, primary_key=True)
    solution_id = Column(Integer, ForeignKey('solutions.id'))
    body = Column(String)
    user_id = Column(String, ForeignKey('users.id'))
    submission_time = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def exists(db_session, solution_comment_id):
        """Returns True if solution_comment_id exists"""
        solution_comment = db_session.query(SolutionComment).filter(
            SolutionComment.id==solution_comment).first()
        return solution_comment is not None


Base.metadata.create_all(engine)

