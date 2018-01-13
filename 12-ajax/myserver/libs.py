import os
import urllib.parse


def normalize_path(path):
    path, _, query = path.partition('?')
    path = urllib.parse.unquote(path)
    path_parts = path.split('/')

    head_parts = []
    for part in path_parts[:-1]:
        if part == '..':
            head_parts.pop()
        elif part and part != '.':
            head_parts.append(part)

    if path_parts:
        tail_part = path_parts.pop()
        if tail_part:
            if tail_part == '..':
                head_parts.pop()
                tail_part = ''
            elif tail_part == '.':
                tail_part = ''
    else:
        tail_part = ''

    if query:
        tail_part = '?'.join((tail_part, query))

    splitpath = ('/' + '/'.join(head_parts), tail_part)
    collapsed_path = "/".join(splitpath)

    return collapsed_path


def is_python(path):
    head, tail = os.path.splitext(path)
    return tail.lower() in (".py", ".pyw")


def is_executable(path):
    return executable(path)

def executable(path):
    return os.access(path, os.X_OK)