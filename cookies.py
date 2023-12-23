import socket
import os
SESSIONS = {}


def check_session(headers):

    headers = {k: v for k, v in (line.split(': ') for line in headers)}

    cookies = parse_cookies(headers.get('Cookie', ''))

    session_id = cookies.get('session_id')
    if not session_id or session_id not in SESSIONS:
        print("No session")
        return 
    print("Check session pass, username = " + SESSIONS[session_id]["username"])
    return SESSIONS[session_id]["username"]

    
def parse_cookies(cookie_string):
    cookies = {}
    if cookie_string:
        for cookie in cookie_string.split(';'):
            if '=' not in cookie:
                continue
            key, value = cookie.split('=', 1)
            cookies[key.strip()] = value.strip()
    return cookies

def create_session(username):
    session_id = os.urandom(16).hex()
    SESSIONS[session_id] = {"username": username}
    print("Session created for user: " + username)
    return session_id

