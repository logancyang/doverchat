import logging
import os
import time
import functools

from flask import request
from flask import Flask, render_template
from flask_login import current_user, LoginManager
from flask_socketio import SocketIO, emit, disconnect

from models import User

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

# login_manager = LoginManager()
# # 'strong' logs user out if it detects different browser or ip
# login_manager.session_protection = 'strong'
# login_manager.init_app(app)
# login_manager.login_view = 'login'

socketio = SocketIO(app, cors_allowed_origins='*')


@app.route('/')
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
# @authenticated_only
def chat_broadcast(msg):
    curr_time = time.time_ns()//1000000
    msg_obj = {
        'timestamp': f'{curr_time}',
        'username': msg['username'],
        'data': msg['data']
    }
    logger.info('broadcast msg_obj:', msg_obj)
    emit('my_response', msg_obj, broadcast=True)

@socketio.on('connect', namespace='/chat')
def chat_connect():
    # if current_user.is_authenticated:
        emit('my_response', {'data': 'Connected'})
    # else:
    #     logger.error("Curreny user is not authenticated: %s" % current_user)
    #     return False

@socketio.on('disconnect', namespace='/chat')
def chat_connect():
    logger.info('Client disconnected')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8100, debug=True)
