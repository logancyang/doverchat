import os
from pathlib import Path
from dotenv import load_dotenv

path = Path(os.path.dirname(__file__))
parentdir = path.parent
load_dotenv(parentdir/'.env')
SECRET_KEY = os.environ.get('SECRET_KEY')
