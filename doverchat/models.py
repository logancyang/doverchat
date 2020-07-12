from flask_login import UserMixin
from sqlalchemy import Column, Integer, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Message(Base):
    __tablename__ = 'doverchat_messages'

    id = Column(Integer, primary_key=True)
    # Time properties
    created_at = Column(BigInteger)

    # Message properties
    message_text = Column(String)
    room_code = Column(String)

    # User properties
    user_name = Column(String)
    user_screen_name = Column(String)
    href = Column(String)

    # __init__() is taken care of by Base
    def __repr__(self):
        return (f"<Message("
                f"id={self.id}, "
                f"created_at={self.created_at}, "
                f"message_text={self.message_text}, "
                f"user_name={self.user_name}, "
                f"user_screen_name={self.user_screen_name}, "
                f"room_code={self.room_code}",
                f"href={self.href}",
                ")>")


class Room(Base):
    __tablename__ = 'doverchat_rooms'

    id = Column(Integer, primary_key=True)
    room_code = Column(String)
    room_screen_name = Column(String)

    # __init__() is taken care of by Base
    def __repr__(self):
        return (f"<Room("
                f"room_code={self.room_code}, "
                f"room_screen_name={self.room_screen_name}"
                ")>")


class User(Base):
    __tablename__ = 'doverchat_users'

    username = Column(String, primary_key=True)
    password = Column(String)
    user_screen_name = Column(String)
    userrooms = Column(String) # comma-separated room_code's

    def __repr__(self):
        return (f"<User("
                f"username={self.username}, "
                f"user_screen_name={self.user_screen_name}, "
                f"userrooms={self.userrooms}"
                ")>")


class LoginUser(UserMixin):
    def __init__(self, username, password):
        super().__init__()
        self.id = username
        self.password = password

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, new_password):
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        self._password = new_password
