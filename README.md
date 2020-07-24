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

#### Use Python 3.6.8

- Heroku: set `python-3.6.8` in `runtime.txt`
- EB: Pick the platform at environment creation time. Or use the environment home page to change the platform (big button on the right).

#### Use Docker, EB CLI and Application load balancer

Since I have some env variables, I need to use `eb create --envvars KEY1=VALUE1 KEY2=VALUE2 ...` to create the environment. The UI way of setting env variables doesn't work after the environment creation.

Another issue is websocket support. Classic load balancer does not support websocket natively. Use application load balancer. This is also only configurable at environment creation. Use `eb create` with `--elb-type application`.
