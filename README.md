## DoverChat

This is a private chat app based on Flask-SocketIO, vanilla JS and Bootstrap, and AWS RDS Postgres. An invite token is required to join.

TODO: build client using React Native for mobile.

### Deployment: Heroku

Heroku requires `requirements.txt` to recognize the Python app. It also needs `runtime.txt` to specify a Python version, or it uses default version 3.6.8.

### Network

It turns out that the Heroku deployment is fast for users in the US, but very slow for China. Tried AWS west region Elastic Beanstalk deployment and also not fast enough for socketio based chat. Need other solutions.
