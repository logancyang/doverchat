## DoverChat

This is a private chat app based on Flask-SocketIO, vanilla JS, Bootstrap, and AWS DynamoDB (RDS Postgres integration also available). An invite token is required to join.

TODO: rebuild client using React, and React Native for mobile.

### Deployment: Heroku

Heroku requires `requirements.txt` to recognize the Python app. It also needs `runtime.txt` to specify a Python version, or it uses default version 3.6.8.

### Deployment: Elastic Beanstalk

For AWS Elastic Beanstalk, must set environment variable `PORT` to make it work.

Use `eb` CLI to `init`, `create` the environment. Use `eb deploy` to deploy.

### Issues

Flask-socketio has dependency issue with eventlet on Python 3.7+, so switched to python 3.6.8 https://github.com/eventlet/eventlet/issues/526

To use Python 3.6.8

- Heroku: set `python-3.6.8` in `runtime.txt`
- EB: Pick the platform at environment creation time. Or use the environment home page to change the platform (big button on the right).
