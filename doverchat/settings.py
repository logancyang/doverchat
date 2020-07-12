import os
from pathlib import Path
from dotenv import load_dotenv

path = Path(os.path.dirname(__file__))
parentdir = path.parent
load_dotenv(parentdir/'.env')
SECRET_KEY = os.environ.get('SECRET_KEY')
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION')
POSTGRES_RDS_URL = os.environ.get('POSTGRES_RDS_URL')

# ADMIN room is for me to check logging messages
ADMIN = "ADMIN"
ROOMS = ["EVLO", ADMIN,
    "母与子", "evlo+mom", "星韵虎威"
    "父与子", "evlo+dad", "丹耀集团"]

# Default room for each user is the first one
ROOM_MAP = {
    "yangchao": ROOMS,
    "wuyunlin": ["EVLO", "evlo+mom", "星韵虎威", "evlo+dad", "丹耀集团"],
    "zhaoyouxing": ["母与子", "evlo+mom", "星韵虎威"],
    "yangjianjun": ["父与子", "evlo+dad"],
    "lidanxia": ["丹耀集团"],
    "wuyaoxin": ["丹耀集团"]
}
