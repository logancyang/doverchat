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
from .models import LoginUser, User, Room
from .query import query_user, query_rooms, query_users
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


def _get_room_map():
    with session_scope() as session:
        rooms_q = query_rooms()
        room_objs = session.query(Room).from_statement(text(rooms_q)).all()
        room_map = {}
        for room_obj in room_objs:
            room_map[room_obj.room_code] = room_obj.room_screen_name
        return room_map


def _get_room_access_list(username):
    """Get the room screen names for this user"""
    with session_scope() as session:
        user_q = query_user(username)
        user_obj = session.query(User)\
            .from_statement(text(user_q)).first()
        room_codes = user_obj.userrooms.split(', ')
        room_map = _get_room_map()
        return [room_map[room_code] for room_code in room_codes]


def _get_user_screen_name(username):
    with session_scope() as session:
        q = query_user(username)
        user_obj = session.query(User).from_statement(text(q)).first()
        return user_obj.user_screen_name


def _get_all_users():
    """Get all user"""
    with session_scope() as session:
        user_q = query_users()
        user_list = session.query(User)\
            .from_statement(text(user_q)).all()
        return [user_obj.username for user_obj in user_list]


def _get_user_creds(username):
    """Get the credentials for this user"""
    with session_scope() as session:
        user_q = query_user(username)
        user_obj = session.query(User)\
            .from_statement(text(user_q)).first()
        return user_obj.password


"""
Login
"""


@login_manager.user_loader
def user_loader(username):
    valid_users = _get_all_users()
    if username not in valid_users:
        return

    password = _get_user_creds(username)
    userlogin = LoginUser(username, password)
    return userlogin


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    valid_users = _get_all_users()
    if username not in valid_users:
        return

    password = _get_user_creds(username)
    userlogin = LoginUser(username, password)
    userlogin.is_authenticated = (request.form['password'] == password)
    return userlogin


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        username = request.form['username']
        valid_users = _get_all_users()
        if username not in valid_users:
            logger.info(
                "Client entered wrong username! Attemped username: %s,"
                "password: %s" % (username, request.form['password'])
            )
            flash("错误的用户名或密码")
            return unauthorized_handler()
        password = _get_user_creds(username)
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
        room_access_list = _get_room_access_list(username)
        return app.response_class(
            response=json.dumps(room_access_list),
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
    msg_obj = {
        'timestamp': f'{curr_time}',
        'username': username,
        'user_screen_name': _get_user_screen_name(username),
        'data': msg['data'],
        'room': msg['room']
    }
    logger.info('broadcast msg_obj %s \nin room %s:'
                % (msg_obj, msg['room']))
    emit('my_response', msg_obj, room=msg['room'])


@socketio.on('join')
@authenticated_only
def on_join(msg):
    username = current_user.get_id()
    room = msg['room']
    user_screen_name = _get_user_screen_name(username)
    enter_msg = user_screen_name + '加入了房间: ' + room
    denied_msg = user_screen_name +\
        ' attempted to join room but denied: ' + room
    curr_time = time.time_ns()//1000000
    msg_obj = {
        'timestamp': f'{curr_time}',
        'username': current_user.get_id(),
        'user_screen_name': user_screen_name,
        'data': enter_msg,
        'room': room
    }
    room_access_set = set(_get_room_access_list(username))
    if room not in room_access_set:
        logger.error(denied_msg)
        msg_obj['data'] = denied_msg
        emit('my_response', msg_obj, room='ADMIN')
        return

    join_room(room)
    emit('my_response', msg_obj, room=room)


@socketio.on('leave')
@authenticated_only
def on_leave(msg):
    username = current_user.get_id()
    room = msg['room']
    leave_room(room)
    emit('user_left', username + ' has left the room: ' + room, room=room)


@socketio.on('connect')
@authenticated_only
def chat_connect():
    if current_user.is_authenticated:
        logger.info('Client connected, user: %s' % current_user.get_id())
        emit(
            'my_response',
            {'data': f'{current_user.get_id()} connected'},
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
