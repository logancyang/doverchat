import os
from pathlib import Path
from dotenv import load_dotenv

path = Path(os.path.dirname(__file__))
parentdir = path.parent
load_dotenv(parentdir/'.env')
SECRET_KEY = os.environ.get('SECRET_KEY')

# ADMIN room is for me to check logging messages
ADMIN = "ADMIN"
ROOMS = ["EVLO", ADMIN,
    "LOZYX", "EVLOZYX", "EVLOZYXZWY"
    "LOYJJ", "EVLOYJJ", "EVLOWU"]

# Default room for each user is the first one
ROOM_MAP = {
    "yangchao": ROOMS,
    "wuyunlin": ["EVLO", "EVLOZYX", "EVLOZYXZWY", "EVLOYJJ", "EVLOWU"],
    "zhaoyouxing": ["LOZYX", "EVLOZYX", "EVLOZYXZWY"],
    "yangjianjun": ["LOYJJ", "EVLOYJJ"],
    "lidanxia": ["EVLOWU"],
    "wuyaoxin": ["EVLOWU"]
}
