The Broadcaster
===============

Overview
--------

The primary purpose of this software was to broadcast shell commands to multiple
machines simultaneously. In order to do this, it was important to us that a
rogue server could not pretend to be us and that only someone with direct access
to the server would have access to the broadcasting mechanism.

The server is very simple: it waits for three events---standard input,
connections and reads from active connections:

* Standard input gets redirected to all active connections

* On new connections, an SSL handshake happens, and the connection is marked
active.

* On reads from active connections, the data is simply flushed, although it
could be used for other purposes (this is the main reason we even listen for
this event).

To enforce the fact that the clients should only connect to a single server, a
Certificate Authority is created, and used to sign server certificates. The key
to the CA is then encrypted and stored safely (you should only ever need it if
you want other servers to act as broadcasters). The server certificates
authenticate the server as legitimate in the eyes of the authority. The client
will not connect to any server that does not have a legitimate certificate.

To enforce that direct access to the server is required for broadcasting, the
server is only setup to broadcast commands inserted into stdin. This is a very
soft requirement, as stdin can be piped through netcat or other processes
providing network/remote access support. SSH is another viable option. This
requirement was not a priority, so there is no stricter checking.

Installing
----------

To run the server and clients, you only need python's SSL library, and openssl
installed. To create the certificates you only need openssl and pgp to encrypt
an archive containing them.

### Installing Certificates

The script `./install_certificates.sh` will setup a new certificate authority
and create server certificates. This script will prompt you for a password to
encrypt all the files that you should not release. All the files that should not
be released to the public are stored in `confidential.tar.xz.enc` (encrypted
version with your password) and in the `confidential/` directory for usage.
During the install you'll be prompted for information to put under your
certificates. The script is very much based on what's written [here][certguide].

Your server needs that `confidential/` directory to be unencrypted and present,
but your clients do not need it, they only need the root Certificate Authority
which will be located in the same directory as the `./install_certificates.sh`
script, under the name `rootCA.pem`.

If you have your own signed certificates by an existing Certificate Authority,
you do not need to create new certificates and may use those via the parameters:

* `-c,--cert certificate_file` specify an existing certificate file
* `-k,--key key_file` specify an existing key file
* `-a,--ca ca_file` specify an existing Certificate Authority (optional)

The `./client.sh` script for your clients will use by default a file named
`rootCA.pem` in the same directory it's running from. It can be passed a
different CA as an argument, however, it is simply the second argument it
optionally gets (the first argument is the server host:port). For example, if
you want to run it with customCA.pem as its Certificate Authority, you can do:

```bash
./client.sh $HOST:$PORT customCA.pem
```

If you need your certificate files that are in confidential back from the
encrypted archive, you can run `./decrypt.sh` to decrypt them (it will ask
you for the same passphrase you used when running `./install_certificates.sh`).

Make sure that the information on your certificates differs from the one on
your Certificate Authority, otherwise the connection will fail due to self
signed certificates.

During the filling out of information for your server certificate you will be
asked to optionally fill out a password and optional company name. You are not
required to do this.

Usage
-----

The `./server.py` script has a help menu that displays all the options it
supports:

```bash
Usage:
./server.py [-p --port port_number] [-c --cert certificate_file] [-k --key key_file] [-a --ca ca_file] [-h --help]
[-p --port  Port number to bind to. Default is 6601.]
[-c --cert  Location of certificate file.]
[-k --key   Location of key file.]
[-a --ca    Location of Certificate Authority file.]
[--host     Host the server should bind to.]
[-h --help  Show this help text.]
```

The `./client.sh` file is a simple bash script that uses openssl and piping to
talk to our server and execute commands locally. The logic should be easy to
follow. It retries every second in case the connection fails, since it was
designed to be deployed on machines whose network connection is prone to
intermittent failure. If you generate your certificates using our
`./install_certificates.sh` script, you should just copy the `rootCA.pem` file
to the client machines. The `./client.sh` script is setup to connect to a
server:port that it gets as its first argument

If you want a quick start guide, you can get started with (assumes that the
server's host is broadcast.net):

#### Server
```bash
./install_certificates.sh
./server.py
```

#### Client
Make sure you download the rootCA.pem file generated in the server to the same
directory you're working in now.

```bash
./client.sh broadcast.net
```

You should now be able to control your computers remotely.

[certguide]: http://datacenteroverlords.com/2012/03/01/creating-your-own-ssl-certificate-authority/ "Creating Your Own SSL Certificate Authority (and Dumping Self Signed Certs)"
