## DoverChat

This is a private chat app based on Flask-SocketIO, vanilla JS and Bootstrap, and AWS RDS Postgres. An invite token is required to join.

TODO: build client using React Native for mobile.

### Deployment: Heroku

Heroku requires `requirements.txt` to recognize the Python app. It also needs `runtime.txt` to specify a Python version, or it uses default version 3.6.8.

### Network

It turns out that the Heroku deployment is fast for users in the US, but very slow for China. Tried AWS west region Elastic Beanstalk deployment and also not fast enough for socketio based chat. Need other solutions.

### Elastic Beanstalk

For AWS Elastic Beanstalk, must set environment variable `PORT` to make it work.

Use `eb` CLI to `init`, `create` the environment. Use `eb deploy` to deploy.

### Issues

Flask-socketio has dependency issue with eventlet, so switched to python 3.6.8 https://github.com/eventlet/eventlet/issues/526

Use Python 3.6.8

- Heroku: set `python-3.6.8` in `runtime.txt`
- EB: Pick the platform at environment creation time. Or use the environment home page to change the platform (big button on the right).
