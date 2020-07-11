## DoverChat

This is a private chat app based on Flask-SocketIO, vanilla JS and Bootstrap, and DynamoDB. An invite token is required to join.

The message object:

```py
{
    "username": str,
    "data": str, # The actual message
    "timestamp": time.time(), # float with 2 decimal places
    "room": str, # name of the room
    "to": str, # Optional: the username this message is for, in format `@<username>`
    "ents": list # Optional: list of entities identified by NER
}
```

Where `timestamp` is unix epoch time the server produces. The client shows local time based on it.

### Deployment: Heroku

Heroku requires `requirements.txt` to recognize the Python app. It also needs `runtime.txt` to specify a Python version, or it uses default version 3.6.8.
