import os, sys
import urllib.parse

def _x_requested_with():
    return os.environ.get('X-Requested-With')

def _method():
    return os.environ.get('REQUEST_METHOD')

def _query_arguments():
    return os.environ.get('QUERY_STRING')

def _body_arguments():
    content_length = os.environ.get('CONTENT_LENGTH')
    if content_length:
        return sys.stdin.read(int(content_length))
    return None

def is_xhr():
    if _x_requested_with() == 'XMLHttpRequest':
        return True
    return False

def is_get():
    if _method().upper() == "GET":
        return True
    return False

def is_post():
    if _method().upper() == 'POST':
        return True
    return False

def get_form():
    return urllib.parse.parse_qs(_query_arguments())

def post_form():
    if is_post():
        return urllib.parse.parse_qs(_body_arguments())
    return {}
