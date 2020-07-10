from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, username, password, display_name="DisplayName"):
        super().__init__()
        self.id = username
        self.display_name = display_name
        self.password = password

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, new_password):
        if len(new_password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        self._password = new_password

    @property
    def display_name(self):
        return self._display_name

    @display_name.setter
    def display_name(self, new_display_name):
        self._display_name = new_display_name

