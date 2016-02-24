#!/usr/bin/env python3
import sys
import socket
import ssl
import getopt
import os
import select

DEFAULT_PORT = 6601
DEFAULT_CAFILE = "rootCA.pem"
DEFAULT_CERTFILE = "confidential/server.crt"
DEFAULT_KEY = "confidential/server.key"
DEFAULT_HOST = ''

NAME = sys.argv[0]
argv = sys.argv[1:]


def usage(out=sys.stderr):
    global NAME
    print('''Usage:
    %s [-p --port port_number] [-c --cert certificate_file] [-k --key key_file] [-a --ca ca_file] [-h --help]
    [-p\t--port\tPort number to bind to. Default is 601.]
    -c\t--cert\tLocation of certificate file. Required if no default is set.
    -k\t--key\tLocation of key file. Required if no default is set.
    [-a\t--ca\tLocation of Certificate Authority file.]
    [--host\tHost the server should bind to.]
    -h\t--help\t
''' % NAME, file=out)

opt_to_names = {
    '-p': 'port',
    '-c': 'certfile',
    '-k': 'key',
    '-a': 'cafile',
    '-h': 'help',
    '--port': 'port',
    '--cert': 'certfile',
    '--ca': 'cafile',
    '--key': 'key',
    '--help': 'help'
}
SHORT_OPTIONS = 'p:c:a:k:h'
LONG_OPTIONS = ['port=', 'cert=', 'ca=', 'key=', 'help', 'host=']


def main(argv):
    try:
        options, argv = getopt.gnu_getopt(argv, SHORT_OPTIONS, LONG_OPTIONS)
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    def parse_opt(x):
        return x if x[-1] != '=' else x[:-1]
    opt_to_names = {'--' + parse_opt(opt): parse_opt(opt)
                    for opt in LONG_OPTIONS}
    long_ind = 0
    for i in SHORT_OPTIONS:
        if i == ':':
            continue
        opt_to_names['-'+i] = parse_opt(LONG_OPTIONS[long_ind])
        long_ind += 1

    server_args = dict((opt_to_names[opt_name], opt)
                       for opt_name, opt in options)
    if 'help' in server_args:
        usage(out=sys.stdout)
    else:
        start_server(**server_args)
    sys.exit(0)


def start_server(cert=DEFAULT_CERTFILE, key=DEFAULT_KEY,
                 ca=DEFAULT_CAFILE, port=DEFAULT_PORT, host=DEFAULT_HOST):
    try:
        port = int(port)
        error = False

        if not (0 <= port <= 65535):
            print("Invalid port number", file=sys.stderr)
            error = True

        if cert is None or not os.path.isfile(cert):
            print("Invalid certificate file", file=sys.stderr)
            if key is None:
                print("There is no appropriate default certificate file.",
                      file=sys.stderr)
            error = True

        if key is None or not os.path.isfile(key):
            print("Invalid key file", file=sys.stderr)
            if key is None:
                print("There is no appropriate default key file.",
                      file=sys.stderr)
            error = True

        if ca is not None and not os.path.isfile(ca):
            print("Invalid CA file", file=sys.stderr)
            error = True

        if (error):
            raise getopt.GetoptError("Bad Option")
    except ValueError:
        print("Port number must be integer")
        usage()
        sys.exit(2)
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    print("Starting server at %s:%d\n"
          "Certificate: %s\tKey: %s%s" %
          (host, port, cert, key, '' if ca is None else '\tCA: %s' % ca),
          file=sys.stderr)

    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=ca)
    context.load_cert_chain(certfile=cert, keyfile=key)

    bindsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bindsocket.setblocking(False)
    bindsocket.bind((host, port))
    bindsocket.listen(5)
    connected = set()
    try:
        while True:
            read_list = [sys.stdin, bindsocket] + list(connected)
            readable, _, _ = select.select(read_list, [], [])
            for r in readable:
                if r == sys.stdin:
                    message = sys.stdin.readline()
                    if message == '':
                        return
                    for c in connected:
                        c.send(bytes(message, 'UTF-8'))
                elif r == bindsocket:
                    print("Connection received.", file=sys.stderr)
                    try:
                        conn, fromaddr = bindsocket.accept()
                    except socket.error:
                        print("Error on accept, ignoring.", file=sys.stderr)
                        continue
                    conn.setblocking(True)
                    try:
                        ssl_conn = context.wrap_socket(conn, server_side=True)
                        connected.add(ssl_conn)
                    except (ssl.SSLEOFError, ssl.SSLError,
                            ConnectionResetError):
                        print("Bad SSL connection.", file=sys.stderr)
                else:
                    print("Data received from socket.", file=sys.stderr)
                    try:
                        o = r.read()
                    except ValueError:
                        print("This can rarely happen if someone closes "
                              "connection during accept or handshake start.\n"
                              "Seems to be a bug with SSL or sockets.\n"
                              "We are just removing the socket from our queue "
                              "in this case", file=sys.stderr)
                        connected.remove(r)
                        continue
                    except ConnectionResetError:
                        print("Unsure why this happens, we just cleanly remove "
                              "the socket from our queue in this case.",
                              file=sys.stderr)
                        connected.remove(r)
                    if o == b'':
                        print("Socket closed connection.", file=sys.stderr)
                        connected.remove(r)
                        r.shutdown(socket.SHUT_RDWR)
                        r.close()
    finally:
        print("Cleaning up connections.")
        for c in connected:
            c.shutdown(socket.SHUT_RDWR)
            c.close()

main(argv)
