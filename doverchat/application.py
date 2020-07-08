import os
import logging
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
socketio = SocketIO(app, cors_allowed_origins='*')


@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('my_event', namespace='/chat')
def chat_message(msg):
    logger.info('msg:', msg)
    emit('my_response', {'data': msg['data']})

@socketio.on('my_broadcast_event', namespace='/chat')
def chat_broadcast(msg):
    logger.info('broadcast msg:', msg)
    emit('my_response', {'data': msg['data']}, broadcast=True)

@socketio.on('connect', namespace='/chat')
def chat_connect():
    emit('my_response', {'data': 'Connected'})

@socketio.on('disconnect', namespace='/chat')
def chat_connect():
    logger.info('Client disconnected')


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8100, debug=True)
