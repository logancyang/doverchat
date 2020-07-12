import logging
import os
import psycopg2
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from .settings import POSTGRES_RDS_URL


Base = declarative_base()

class Database:
    def __init__(self, env='dev'):
        """DB setup"""
        # Initialize the database :: Connection & Metadata retrieval
        self.db_url = self._set_db_url_by_env(env)
        self.engine = create_engine(self.db_url, echo=False)

    def create_db_session(self):
        # Create all tables that do not already exist
        Base.metadata.create_all(
            self.engine,
            Base.metadata.tables.values(),
            checkfirst=True
        )
        # SqlAlchemy :: Session setup
        Session = sessionmaker(bind=self.engine)
        # SqlAlchemy :: Starts a session
        return Session()

    def _set_db_url_by_env(self, env='dev'):
        db_url = 'sqlite:///' + os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'db.sqlite')
        # format: (user):(password)@(db_identifier).amazonaws.com:5432/(db_name)
        if env == 'prod':
            db_url = POSTGRES_RDS_URL
        return db_url
