import decimal
import json
import logging
import time
import functools

import boto3
from boto3.dynamodb.conditions import Key
from flask import Flask, flash, render_template, request, redirect, url_for
from flask_login import current_user, LoginManager, login_required, \
    login_user, logout_user
from flask_socketio import SocketIO, emit, disconnect, join_room, \
    leave_room

from doverchat.models import LoginUser
from doverchat.settings import SECRET_KEY, AWS_ACCESS_KEY_ID, \
    AWS_SECRET_ACCESS_KEY, AWS_REGION


session = boto3.session.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION
)
dynamodb = session.resource('dynamodb')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
application = app

login_manager = LoginManager()
# 'strong' logs user out if it detects different browser or ip
login_manager.session_protection = 'strong'
login_manager.init_app(app)

socketio = SocketIO(app, cors_allowed_origins='*')

ROOM_MAP_PATH = "./doverchat/data/room_map.json"
USER_ROOMS_PATH = "./doverchat/data/user_rooms.json"


"""
helpers
"""


def timeit(func):
    """
    Wraps func using wrapper_func that returns the same value
    as func but also add elaspse time
    """
    @functools.wraps(func)
    def wrapper_func(*args, **kwargs):
        before = time.time()
        rv = func(*args, **kwargs)
        after = time.time()
        logger.info("Function {%s} elapsed time: %s" %
                    (func.__name__, after - before))
        return rv
    return wrapper_func


# Helper class to convert a DynamoDB item to JSON.
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, decimal.Decimal):
            return str(o)
        if isinstance(o, set):
            return list(o)
        return super(DecimalEncoder, self).default(o)


def _serialize(data):
    return json.dumps(data, cls=DecimalEncoder)


def _decimal_dict(pydict):
    """Turn created_at into Decimal"""
    created_at = pydict['created_at']
    pydict['created_at'] = decimal.Decimal(created_at)
    return pydict


def _row2dict(row_obj, exclude=None):
    return {
        col.name: str(getattr(row_obj, col.name))
        for col in row_obj.__table__.columns if col.name != exclude}


def _get_room_map():
    with open(ROOM_MAP_PATH, encoding="utf-8") as f:
        room_map = json.load(f)

    room_inverse_map = {}
    for room_code, room_name in room_map.items():
        room_inverse_map[room_name] = room_code
    return room_map, room_inverse_map


@timeit
def _get_room_access_list(user_dict, room_map):
    """Get the room map as a list of 2-tuples for this user"""
    room_codes = user_dict.get('userrooms').split(', ')
    return [(room_code, room_map[room_code]) for room_code in room_codes]


@timeit
def _get_all_user_info():
    """Get all user"""
    with open(USER_ROOMS_PATH, encoding="utf-8") as f:
        user_list = json.load(f)
    return {user['username']: user for user in user_list}


@timeit
def _get_last_n_msgs(room_code, n):
    response = MSG_TABLE.query(
        KeyConditionExpression=Key('room_code').eq(room_code)
    )
    raw_msg_list = response['Items']
    return _serialize(raw_msg_list)


"""
In-memory variable loaded once at startup
"""

USER_DICT = _get_all_user_info()
logger.info("USER_DICT loaded into memory")
ROOM_MAP, ROOM_INVERSE_MAP = _get_room_map()
logger.info("ROOM_MAP, ROOM_INVERSE_MAP loaded into memory")
USER_TABLE = dynamodb.Table('doverchat_users')
MSG_TABLE = dynamodb.Table('doverchat_messages')
logger.info("DynamoDB tables declared")


"""
Login
"""


@login_manager.user_loader
def user_loader(username):
    if username not in USER_DICT:
        return

    response = USER_TABLE.get_item(Key={'username': username})
    user = response['Item']
    password = user['password']
    userlogin = LoginUser(username, password)
    return userlogin


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if username not in USER_DICT:
        return

    response = USER_TABLE.get_item(Key={'username': username})
    user = response['Item']
    password = user['password']
    userlogin = LoginUser(username, password)
    userlogin.is_authenticated = (request.form['password'] == password)
    return userlogin


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        username = request.form['username']
        if username not in USER_DICT:
            logger.info(
                "Client entered wrong username! Attemped username: %s,"
                % username
            )
            flash("错误的用户名或密码")
            return unauthorized_handler()

        response = USER_TABLE.get_item(Key={'username': username})
        user = response['Item']
        password = user['password']

        if request.form['password'] == password:
            userlogin = LoginUser(username, password)
            login_user(userlogin)
            logger.info('Client successfully logged in, user: %s', username)
            curr_time = int(time.time()*1000)
            msg_dict = {
                'created_at': curr_time,
                'message_text': f"{username} has logged in.",
                'username': username,
                'user_screen_name': USER_DICT[username]['user_screen_name'],
                'room_code': 'ADMIN'
            }
            MSG_TABLE.put_item(Item=_decimal_dict(msg_dict))
            return redirect(url_for('index'))

        logger.info(
            "Client entered wrong password! Attemped username: %s,"
            "password: %s" % (username, request.form['password']))
        flash("错误的用户名或密码")
        return unauthorized_handler()


@app.route('/logout')
@login_required
def logout():
    logger.info('Client logged out, user: %s' % current_user.get_id())
    logout_user()
    return redirect(url_for('login'))


@login_manager.unauthorized_handler
def unauthorized_handler():
    return redirect(url_for('login'))


"""
Views and sockets
"""


@app.route('/')
@login_required
def index():
    return render_template('index.html')


def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped


@app.route('/userrooms')
@authenticated_only
def get_user_rooms():
    if current_user.is_authenticated:
        username = current_user.get_id()
        room_access_list = _get_room_access_list(USER_DICT[username], ROOM_MAP)
        return application.response_class(
            response=json.dumps(room_access_list),
            status=200,
            mimetype='application/json'
        )
    else:
        logger.error(
            "Current user is not authenticated: %s" % current_user.get_id())
        return False


@app.route('/updatepassword', methods=['GET', 'POST'])
def update_password():
    if request.method == 'GET':
        return render_template('update.html')

    if request.method == 'POST':
        username = request.form['username']
        if username not in USER_DICT:
            logger.info(
                "Client entered wrong username! Attemped username: %s,"
                % username
            )
            flash("错误的用户名。如忘记用户名请联系logancyang AT gmail")
            return redirect(url_for('update_password'))

        response = USER_TABLE.get_item(Key={'username': username})
        user = response['Item']
        old_password = user['password']

        if request.form['old_password'] == old_password:
            new_password = request.form['new_password']
            confirm_new_password = request.form['confirm_new_password']
            if len(new_password.strip()) < 8:
                flash("新密码不能含有空格，至少8个字符")
                return redirect(url_for('update_password'))
            if new_password == old_password:
                flash("新密码必须不同于旧密码")
                return redirect(url_for('update_password'))
            if confirm_new_password != new_password:
                flash("确认新密码与新密码输入不符，请重新输入")
                return redirect(url_for('update_password'))

            # Apply password length check
            LoginUser(username, password=new_password)
            # Update user record in db
            USER_TABLE.put_item(Item={
                'username': username,
                'password': new_password
            })
            # Log message to ADMIN room
            curr_time = int(time.time()*1000)
            msg_dict = {
                'created_at': curr_time,
                'message_text': f"{username} has updated password.",
                'username': username,
                'user_screen_name': USER_DICT[username]['user_screen_name'],
                'room_code': 'ADMIN'
            }
            MSG_TABLE.put_item(Item=_decimal_dict(msg_dict))

            logger.info(
                'Client successfully updated password, username: %s',
                username
            )
            flash("密码更新成功！")
            return redirect(url_for('login'))

        logger.info(
            "Client entered wrong old password when attempting to "
            "update password! Attemped username: %s" % username)
        flash("旧密码有误，请重新输入")
        return redirect(url_for('update_password'))


@app.route('/last-msgs')
@authenticated_only
def get_last_n_messages():
    if current_user.is_authenticated:
        room_code = request.args.get('room_code')
        n = request.args.get('n') or 20
        last_msgs = _get_last_n_msgs(room_code, n)
        return app.response_class(
            response=last_msgs,
            status=200,
            mimetype='application/json'
        )
    else:
        logger.error(
            "Current user is not authenticated: %s" % current_user.get_id())
        return False


@socketio.on('broadcast_event')
@authenticated_only
def chat_broadcast(msg):
    curr_time = int(time.time()*1000)
    username = current_user.get_id()
    room_code = msg['room_code']
    user_screen_name = USER_DICT[username].get('user_screen_name', username)
    msg_dict = {
        'created_at': f'{curr_time}',
        'username': username,
        'user_screen_name': user_screen_name,
        'message_text': msg['message_text'],
        'room_code': room_code
    }
    emit('my_response', msg_dict, room=room_code)
    logger.info('[CHAT BROADCAST] broadcast msg %s \nin room %s:'
                % (msg_dict, room_code))
    MSG_TABLE.put_item(Item=_decimal_dict(msg_dict))


@socketio.on('join')
@authenticated_only
def on_join(msg):
    """ADMIN room has join room info but not realtime socket message"""
    username = current_user.get_id()
    room_code = msg['room_code']
    enter_msg = username + ' joined room: ' + ROOM_MAP[room_code]
    denied_msg = username + ' attempted to join room but denied: '\
        + ROOM_MAP[room_code]
    curr_time = int(time.time()*1000)
    msg_dict = {
        'created_at': f'{curr_time}',
        'username': username,
        'user_screen_name': USER_DICT[username].get('user_screen_name'),
        'message_text': enter_msg,
        'room_code': 'ADMIN'
    }
    room_access_tuples = _get_room_access_list(USER_DICT[username], ROOM_MAP)
    room_access_set = set([tup[0] for tup in room_access_tuples])
    if room_code not in room_access_set:
        logger.error(denied_msg)
        msg_dict['message_text'] = denied_msg
        MSG_TABLE.put_item(Item=_decimal_dict(msg_dict))
        return

    join_room(room_code)
    logger.info('[JOIN ROOM]: ' + enter_msg)
    MSG_TABLE.put_item(Item=_decimal_dict(msg_dict))


@socketio.on('leave')
@authenticated_only
def on_leave(msg):
    username = current_user.get_id()
    room_code = msg['room_code']
    leave_room(room_code)
    emit('user_left',
         username + ' has left the room: ' + room_code, room=room_code)


@socketio.on('connect')
@authenticated_only
def chat_connect():
    if current_user.is_authenticated:
        logger.info('Client connected, user: %s' % current_user.get_id())
    else:
        logger.error(
            "Current user is not authenticated: %s" % current_user.get_id())
        return False


@socketio.on('disconnect')
@authenticated_only
def chat_disconnect():
    logger.info('Client disconnected, user: %s' % current_user.get_id())


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8100, debug=True)
