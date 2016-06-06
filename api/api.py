import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, \
    DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine('sqlite:///api/riker.db')
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    phash = Column(LargeBinary)
    creation_time = Column(DateTime, default=datetime.utcnow)

class ApiSession(Base):
    __tablename__= 'api_session'
    user_id = Column(String, ForeignKey('users.id'))
    key = Column(LargeBinary, default=partial(os.urandom, 16), primary_key=True)
    expire_time = Column(DateTime, lambda: datetime.utcnow() + timedelta(days=30))

