import json
import logging
import os
import time
import functools

import flask
from flask import Flask, flash, render_template, request, redirect, url_for
from flask_login import current_user, LoginManager, login_required, \
    login_user, logout_user
from flask_socketio import SocketIO, emit, disconnect, join_room, \
    leave_room

from .models import User
from .settings import SECRET_KEY, ADMIN, ROOMS, ROOM_MAP

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

login_manager = LoginManager()
# 'strong' logs user out if it detects different browser or ip
login_manager.session_protection = 'strong'
login_manager.init_app(app)

socketio = SocketIO(app, cors_allowed_origins='*')
USERS = {
    'yangchao': {'password': '12345678', 'display_name': '杨超'},
    'wuyunlin': {'password': '87654321', 'display_name': '伍韵琳'},
    'zhaoyouxing': {'password': '12345678', 'display_name': '赵有星'},
    'yangjianjun': {'password': '12345678', 'display_name': '杨建军'}
}

"""
Login
"""

@login_manager.user_loader
def user_loader(username):
    if username not in USERS:
        return

    password = USERS[username].get('password')
    display_name = USERS[username].get('display_name')
    user = User(username, password, display_name)
    return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if username not in USERS:
        return

    password = USERS[username].get('password')
    display_name = USERS[username].get('display_name')
    user = User(username, password, display_name)
    user.is_authenticated = \
        request.form['password'] == USERS[username].get('password')
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        username = request.form['username']
        if username not in USERS:
            logger.info('Client entered wrong username! Attemped username: %s, password: %s' % (username, request.form['password']))
            flash("错误的用户名或密码")
            return unauthorized_handler()
        password = USERS[username]['password']
        if request.form['password'] == password:
            display_name = USERS[username].get('display_name')
            user = User(username, password, display_name)
            login_user(user)
            logger.info('Successfully logged in, user: %s', username)
            return redirect(url_for('index'))

        logger.info('Client entered wrong password! Attemped username: %s, password: %s' % (username, request.form['password']))
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
        rooms = ROOM_MAP[username]
        response = app.response_class(
                response=json.dumps(rooms),
                status=200,
                mimetype='application/json'
            )
        return response
    else:
        logger.error(
            "Current user is not authenticated: %s" % current_user.get_id())
        return False

@socketio.on('broadcast_event')
@authenticated_only
def chat_broadcast(msg):
    curr_time = time.time_ns()//1000000
    msg_obj = {
        'timestamp': f'{curr_time}',
        'username': current_user.get_id(),
        'data': msg['data'],
        'room': msg['room']
    }
    logger.info('broadcast msg_obj %s \nin room %s:'\
         % (msg_obj, msg['room']))
    emit('my_response', msg_obj, room=msg['room'])

@socketio.on('join')
@authenticated_only
def on_join(msg):
    username = current_user.get_id()
    room = msg['room']
    join_room(room)
    emit('user_joined', username + ' has entered room: ' + room, room=room)

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
            room=ADMIN)
    else:
        logger.error(
            "Current user is not authenticated: %s" % current_user.get_id())
        return False

@socketio.on('disconnect')
@authenticated_only
def chat_connect():
    logger.info('Client disconnected, user: %s' % current_user.get_id())


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8100, debug=True)
