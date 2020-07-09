from flask_login import UserMixin

class User(UserMixin):
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

