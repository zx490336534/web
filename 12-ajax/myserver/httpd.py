from http.server import HTTPServer
from handlers import CGIHandler


def run(server_class=HTTPServer, handler_class=CGIHandler, **kwargs):
    BIND = kwargs.get('bind', '')
    PORT = kwargs.get('port', 80)
    ADDRESS = (BIND, PORT)

    print('Serving on: %s:%s ...'%(BIND or '0.0.0.0', PORT))
    with server_class(ADDRESS, handler_class) as server:
        server.serve_forever()

if __name__ == '__main__':
    run()