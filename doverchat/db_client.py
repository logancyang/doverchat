import os
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
        db_url = None
        dev_url = 'sqlite:///' + os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'db.sqlite')
        # format: (user):(password)@(db_identifier).amazonaws.com:5432/(db_name)
        prod_path = POSTGRES_RDS_URL
        if env == 'dev':
            print(f"Environment: dev. Using dev db_url: {dev_url}")
            db_url = dev_url
        elif env == 'prod':
            print(f"Environment: prod. Using prod db_url: {prod_path}")
            db_url = prod_path
        else:
            print(f"Environment invalid. Please make sure to set it as dev or prod.")
        return db_url
