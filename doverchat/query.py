"""Query helpers"""


def query_last_n_msgs(room_code, n=20):
    """Query the last n messages for room"""
    return (f"SELECT * FROM doverchat_messages "
            f"WHERE room_code = '{room_code}' "
            f"ORDER BY id DESC LIMIT {str(n)};")


def query_users():
    """Query all valid users"""
    return "SELECT username FROM doverchat_users;"


def query_rooms():
    """Query room codes and names"""
    return ("SELECT * FROM doverchat_rooms;")


def query_room(room_screen_name):
    """Query room code from name"""
    return (f"SELECT * FROM doverchat_rooms "
            f"WHERE room_screen_name = '{room_screen_name}';")
