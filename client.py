#!/usr/bin/python3 -u
import sys
import os
import ssl
import socket
import select

DEFAULT_CAFILE='rootCA.pem'

def main(argv):
    assert len(argv) >= 2
    host,port=argv[1].split(':')
    port = int(port)
    ca = DEFAULT_CAFILE
    if len(argv) > 2:
        ca = argv[2]
    assert os.path.isfile(ca)
    context = ssl.create_default_context(cafile=ca)
    conn = context.wrap_socket(socket.socket(socket.AF_INET),
                               server_hostname=host)
    conn.connect((host,port))
    try:
        while True:
            read_list,_,_ = select.select([sys.stdin,conn],[],[])
            for r in read_list:
                if r == conn:
                    o = r.read()
                    if o == b'':
                        return 0
                    sys.stdout.write(o.decode("utf-8"))
                else:
                    conn.send(bytes(sys.stdin.readline(), 'UTF-8'))
    finally:
        conn.close()

sys.exit(main(sys.argv))
