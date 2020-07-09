import logging
import os
import time
import functools

import flask
from flask import Flask, render_template, request, redirect, url_for
from flask_login import current_user, LoginManager, login_required, \
    login_user, logout_user
from flask_socketio import SocketIO, emit, disconnect

from models import User
from settings import SECRET_KEY

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
    'yangchao': {'password': '12345678'},
    'wuyunlin': {'password': '87654321'}
}


@login_manager.user_loader
def user_loader(username):
    if username not in USERS:
        return

    password = USERS[username].get('password')
    user = User(username, password)
    return user

@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    if username not in USERS:
        return

    password = USERS[username].get('password')
    user = User(username, password)
    user.is_authenticated = \
        request.form['password'] == USERS[username].get('password')
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        username = request.form['username']
        password = USERS[username]['password']
        if request.form['password'] == password:
            user = User(username, password)
            login_user(user)
            logger.info('Successfully logged in, user: %s', username)
            return redirect(url_for('index'))

        return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('logout'))

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized'

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

@socketio.on('broadcast_event', namespace='/chat')
@authenticated_only
def chat_broadcast(msg):
    curr_time = time.time_ns()//1000000
    msg_obj = {
        'timestamp': f'{curr_time}',
        'username': current_user.id,
        'data': msg['data']
    }
    logger.info('broadcast msg_obj:', msg_obj)
    emit('my_response', msg_obj, broadcast=True)

@socketio.on('connect', namespace='/chat')
@authenticated_only
def chat_connect():
    if current_user.is_authenticated:
        logger.info('Client connected, user: %s' % current_user.id)
        emit('my_response', {'data': 'Connected'})
    else:
        logger.error("Current user is not authenticated: %s" % current_user.id)
        return False

@socketio.on('disconnect', namespace='/chat')
@authenticated_only
def chat_connect():
    logger.info('Client disconnected, user: %s' % current_user.id)


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8100, debug=True)
