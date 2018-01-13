import os, sys
from http.server import SimpleHTTPRequestHandler, HTTPStatus
import copy
import urllib.parse
import base64, binascii
import subprocess
import select

import libs


class CGIHandler(SimpleHTTPRequestHandler):
    rbufsize = 0
    cgi_dirs = ['/cgi-bin', '/htbin']

    def send_head(self):
        if self.is_in_cgi_dir():
            self.run_cgi()
        else:
            return SimpleHTTPRequestHandler.send_head(self)

    def do_POST(self):
        if self.is_in_cgi_dir():
            self.run_cgi()
        else:
            self.send_error(HTTPStatus.NOT_IMPLEMENTED, "Can only POST to CGI scripts")

    def is_in_cgi_dir(self):
        path = self.path
        normalized_path = libs.normalize_path(path)
        dir_sep = normalized_path.find('/', 1)
        head, tail = normalized_path[:dir_sep], normalized_path[dir_sep + 1:]
        if head in self.cgi_dirs:
            self.cgi_info = head, tail
            return True
        return False


    def is_cgi_script(self):
        dir, rest = self.cgi_info
        path = dir + '/' + rest
        i = path.find('/', len(dir) + 1)

        while i >= 0:
            nextdir = path[:i]
            nextrest = path[i + 1:]
            scriptdir = self.translate_path(nextdir)
            if os.path.isdir(scriptdir):
                dir, rest = nextdir, nextrest
                i = path.find('/', len(dir) + 1)
            else:
                break

        rest, _, query = rest.partition('?')

        i = rest.find('/')
        if i >= 0:
            script, rest = rest[:i], rest[i:]
        else:
            script, rest = rest, ''

        scriptname = dir + '/' + script
        scriptfile = self.translate_path(scriptname)

        self.script_info = scriptname, scriptfile, rest, query

        if not os.path.exists(scriptfile):
            self.send_error(HTTPStatus.NOT_FOUND, "No such CGI script (%r)" % scriptname)
            return False

        if not os.path.isfile(scriptfile):
            self.send_error(HTTPStatus.FORBIDDEN, "CGI script is not a plain file (%r)" % scriptname)
            return False

        if not libs.is_python(scriptname):
            if not libs.is_executable(scriptfile):
                self.send_error(HTTPStatus.FORBIDDEN, "CGI script is not executable (%r)" % scriptname)
                return False

        return True


    def build_cgi_environ(self):
        scriptname, scriptfile, rest, query = self.script_info

        env = copy.deepcopy(os.environ)

        env['SERVER_SOFTWARE'] = self.version_string()
        env['SERVER_NAME'] = self.server.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PROTOCOL'] = self.protocol_version
        env['SERVER_PORT'] = str(self.server.server_port)
        env['REQUEST_METHOD'] = self.command

        uqrest = urllib.parse.unquote(rest)
        env['PATH_INFO'] = uqrest

        env['PATH_TRANSLATED'] = self.translate_path(uqrest)
        env['SCRIPT_NAME'] = scriptname

        if query:
            env['QUERY_STRING'] = query

        env['REMOTE_ADDR'] = self.client_address[0]

        if self.headers.get('X-Requested-With'):
            env['X-Requested-With'] = self.headers.get('X-Requested-With')


        authorization = self.headers.get("authorization")
        if authorization:
            authorization = authorization.split()
            if len(authorization) == 2:
                env['AUTH_TYPE'] = authorization[0]
                if authorization[0].lower() == "basic":
                    try:
                        authorization = authorization[1].encode('ascii')
                        authorization = base64.decodebytes(authorization).decode('ascii')
                    except (binascii.Error, UnicodeError):
                        pass
                    else:
                        authorization = authorization.split(':')
                        if len(authorization) == 2:
                            env['REMOTE_USER'] = authorization[0]


        if self.headers.get('content-type') is None:
            env['CONTENT_TYPE'] = self.headers.get_content_type()
        else:
            env['CONTENT_TYPE'] = self.headers['content-type']

        length = self.headers.get('content-length')
        if length:
            env['CONTENT_LENGTH'] = length

        referer = self.headers.get('referer')
        if referer:
            env['HTTP_REFERER'] = referer

        accept = []
        for line in self.headers.getallmatchingheaders('accept'):
            if line[:1] in "\t\n\r ":
                accept.append(line.strip())
            else:
                accept = accept + line[7:].split(',')
        env['HTTP_ACCEPT'] = ','.join(accept)

        ua = self.headers.get('user-agent')
        if ua:
            env['HTTP_USER_AGENT'] = ua

        co = filter(None, self.headers.get_all('cookie', []))
        cookie_str = ', '.join(co)
        if cookie_str:
            env['HTTP_COOKIE'] = cookie_str


        for k in ('QUERY_STRING', 'REMOTE_HOST', 'CONTENT_LENGTH', 'HTTP_USER_AGENT', 'HTTP_COOKIE', 'HTTP_REFERER'):
            env.setdefault(k, "")


        self.send_response(HTTPStatus.OK, "Script output follows")
        self.flush_headers()

        # decoded_query = query.replace('+', ' ')
        return env


    def run_cgi(self):

        if not self.is_cgi_script():
            return

        env = self.build_cgi_environ()

        scriptname, scriptfile, rest, query = self.script_info

        cmdline = [scriptfile]
        if libs.is_python(scriptfile):
            interp = sys.executable
            if interp.lower().endswith("w.exe"):
                interp = interp[:-5] + interp[-4:]
            cmdline = [interp, '-u'] + cmdline

        if '=' not in query:
            cmdline.append(query)
        self.log_message("command: %s", subprocess.list2cmdline(cmdline))

        try:
            nbytes = int(env.get('CONTENT_LENGTH'))
        except (TypeError, ValueError):
            nbytes = 0

        p = subprocess.Popen(cmdline,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             env=env)

        if self.command.lower() == "post" and nbytes > 0:
            data = self.rfile.read(nbytes)
        else:
            data = None

        while select.select([self.rfile._sock], [], [], 0)[0]:
            if not self.rfile._sock.recv(1):
                break

        stdout, stderr = p.communicate(data)
        self.wfile.write(stdout)
        if stderr:
            self.log_error('%s', stderr)
        p.stderr.close()
        p.stdout.close()

        status = p.returncode
        if status:
            self.log_error("CGI script exit status %#x", status)
        else:
            self.log_message("CGI script exited OK")
