import os
from pathlib import Path
from dotenv import load_dotenv

path = Path(os.path.dirname(__file__))
parentdir = path.parent
load_dotenv(parentdir/'.env')
SECRET_KEY = os.environ.get('SECRET_KEY')


ROOMS = ["EVLO",
    "LOZYX", "EVLOZYX", "EVLOZYXZWY"
    "LOYJJ", "EVLOYJJ", "EVLOWU"]

ROOM_MAP = {
    "yangchao": ROOMS,
    "wuyunlin": ["EVLO", "EVLOZYX", "EVLOZYXZWY", "EVLOYJJ", "EVLOWU"],
    "zhaoyouxing": ["LOZYX", "EVLOZYX", "EVLOZYXZWY"],
    "yangjianjun": ["LOYJJ", "EVLOYJJ"],
    "lidanxia": ["EVLOWU"],
    "wuyaoxin": ["EVLOWU"]
}
