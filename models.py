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



engine = create_engine('sqlite:///riker.db')
DBSession = scoped_session(sessionmaker(engine))
Base = declarative_base()



class Problem(Base):
    __tablename__ = 'problems'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    submission_time = Column(DateTime, default=datetime.utcnow)
    title = Column(String)
    prompt = Column(String)
    test_input = Column(String)
    test_output = Column(String)
    timeout = Column(Integer, default=3)

    def solved_by(self, db_session, user_id):
        """Returns True if this problem has been solved by user_id"""
        solutions = (
            db_session.query(Solution)
            .filter(Solution.user_id == user_id)
            .filter(Solution.problem_id == self.id)
            .filter(Solution.verification == 'PASS')
            .first()
        )
        return solutions is not None

    @staticmethod
    def exists(db_session, problem_id):
        """Return True if problem_id exists"""
        problem = db_session.query(Problem).filter(Problem.id==problem_id).first()
        return problem is not None
        

eventlet.monkey_patch() # Required for eventlet to work with Flask
class Solution(Base):
    __tablename__ = 'solutions'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    submission_time = Column(DateTime, default=datetime.utcnow)
    problem_id = Column(Integer, ForeignKey('problems.id'))
    language = Column(String)
    source = Column(String)
    verification = Column(String) # Status string returned by verify.verify

    problem = relationship('Problem')

    def verify(self):
        Solution._verify(self.id)

    _verify_sem = eventlet.semaphore.Semaphore(1)
    @staticmethod
    def _verify(solution_id):
        """Verifies the correctness of the solution using `verify.verify`.
        Task is launched in a separate thread to avoid stalling the server.
        Verify threads must acquire verify_sem to avoid running too many
        verification jobs at once."""
        def thread():
            db_session = DBSession()
            solution = db_session.query(Solution).filter(
                Solution.id == solution_id).first()
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
    user_id = Column(String)
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
    user_id = Column(String)
    submission_time = Column(DateTime, default=datetime.utcnow)

    @staticmethod
    def exists(db_session, solution_comment_id):
        """Returns True if solution_comment_id exists"""
        solution_comment = db_session.query(SolutionComment).filter(
            SolutionComment.id==solution_comment).first()
        return solution_comment is not None


Base.metadata.create_all(engine)

