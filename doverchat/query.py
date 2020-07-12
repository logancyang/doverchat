"""Query helpers"""


def query_last_n_msgs(room_code, n=20):
    """Query the last n messages for room"""
    return (f"SELECT * FROM doverchat_messages "
            f"WHERE room_code = '{room_code}' "
            f"ORDER BY id DESC LIMIT {str(n)};")


def query_user(username):
    """Query the user attributes"""
    return (f"SELECT * FROM doverchat_users WHERE username = '{username}';")


def query_users():
    """Query all valid users"""
    return "SELECT username FROM doverchat_users;"


def query_rooms():
    """Query room codes and names"""
    return ("SELECT * FROM doverchat_rooms;")
