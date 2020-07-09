

class User():
    def __init__(self, username, password):
        self.username = username
        self.password = password

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, new_password):
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        self._password = new_password

