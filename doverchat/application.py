import json
import logging
import time
import functools
from contextlib import contextmanager

from flask import Flask, flash, render_template, request, redirect, url_for
from flask_login import current_user, LoginManager, login_required, \
    login_user, logout_user
from flask_socketio import SocketIO, emit, disconnect, join_room, \
    leave_room
from sqlalchemy.sql import text

from .db_client import Database
from .models import LoginUser, User, Room, Message
from .query import query_rooms, query_users, query_last_n_msgs
from .settings import SECRET_KEY

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

login_manager = LoginManager()
# 'strong' logs user out if it detects different browser or ip
login_manager.session_protection = 'strong'
login_manager.init_app(app)

socketio = SocketIO(app, cors_allowed_origins='*')


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


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    db = Database('prod')
    session = db.create_db_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error("An db exception has occurred! :: %s" % e)
        session.rollback()
        raise
    finally:
        session.close()


def _row2dict(row_obj):
    return {
        col.name: str(getattr(row_obj, col.name))
        for col in row_obj.__table__.columns}


def _get_room_map():
    with session_scope() as session:
        rooms_q = query_rooms()
        room_objs = session.query(Room).from_statement(text(rooms_q)).all()
        room_map = {}
        room_inverse_map = {}
        for room_obj in room_objs:
            room_map[room_obj.room_code] = room_obj.room_screen_name
            room_inverse_map[room_obj.room_screen_name] = room_obj.room_code
        return room_map, room_inverse_map


@timeit
def _get_room_access_list(user_dict, room_map):
    """Get the room map as a list of 2-tuples for this user"""
    room_codes = user_dict.get('userrooms').split(', ')
    return [(room_code, room_map[room_code]) for room_code in room_codes]


@timeit
def _get_all_user_info():
    """Get all user"""
    with session_scope() as session:
        user_q = query_users()
        user_list = session.query(User)\
            .from_statement(text(user_q)).all()
        return {
            user_obj.username: _row2dict(user_obj)
            for user_obj in user_list
        }


@timeit
def _get_last_n_msgs(room_code, n):
    with session_scope() as session:
        q = query_last_n_msgs(room_code, n)
        msg_objs = session.query(Message).from_statement(text(q)).all()
        return [_row2dict(msg_obj) for msg_obj in msg_objs]


"""
In-memory variable loaded once at startup
"""

USER_DICT = _get_all_user_info()
logger.info("USER_DICT loaded into memory")
ROOM_MAP, ROOM_INVERSE_MAP = _get_room_map()
logger.info("ROOM_MAP, ROOM_INVERSE_MAP loaded into memory")


"""
Login
"""


@login_manager.user_loader
def user_loader(username):
    if username not in USER_DICT:
        return

    password = USER_DICT[username]['password']
    userlogin = LoginUser(username, password)
    return userlogin


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if username not in USER_DICT:
        return

    password = USER_DICT[username]['password']
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
                "password: %s" % (username, request.form['password'])
            )
            flash("错误的用户名或密码")
            return unauthorized_handler()
        password = USER_DICT[username]['password']
        if request.form['password'] == password:
            userlogin = LoginUser(username, password)
            login_user(userlogin)
            logger.info('Successfully logged in, user: %s', username)
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
        return app.response_class(
            response=json.dumps(room_access_list),
            status=200,
            mimetype='application/json'
        )
    else:
        logger.error(
            "Current user is not authenticated: %s" % current_user.get_id())
        return False


@app.route('/last-msgs')
@authenticated_only
def get_last_n_messages():
    if current_user.is_authenticated:
        room_code = request.args.get('room_code')
        n = request.args.get('n') or 20
        last_msgs = _get_last_n_msgs(room_code, n)
        last_msgs.reverse()
        return app.response_class(
            response=json.dumps(last_msgs),
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
    curr_time = time.time_ns()//1000000
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
    # Note that the client doesn't see the room_code, only room name
    logger.info('[CHAT BROADCAST] broadcast msg_obj %s \nin room %s:'
                % (msg_dict, room_code))
    with session_scope() as session:
        msg_obj = Message(
            created_at=curr_time,
            message_text=msg['message_text'],
            username=username,
            user_screen_name=user_screen_name,
            room_code=room_code
        )
        session.add(msg_obj)


@socketio.on('join')
@authenticated_only
def on_join(msg):
    username = current_user.get_id()
    room_code = msg['room_code']
    enter_msg = username + ' joined room: ' + room_code
    denied_msg = username + ' attempted to join room but denied: ' + room_code
    curr_time = time.time_ns()//1000000
    msg_obj = {
        'created_at': f'{curr_time}',
        'username': current_user.get_id(),
        'user_screen_name': USER_DICT[username]
                                .get('user_screen_name', username),
        'message_text': enter_msg,
        'room_code': room_code
    }
    room_access_tuples = _get_room_access_list(USER_DICT[username], ROOM_MAP)
    room_access_set = set([tup[0] for tup in room_access_tuples])
    if room_code not in room_access_set:
        logger.error(denied_msg)
        msg_obj['message_text'] = denied_msg
        emit('my_response', msg_obj, room='ADMIN')
        return

    join_room(room_code)
    logger.info('[JOIN ROOM]: ' + enter_msg)
    emit('my_response', msg_obj, room='ADMIN')


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
        emit(
            'my_response',
            {'message_text': f'{current_user.get_id()} connected'},
            room='ADMIN')
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
