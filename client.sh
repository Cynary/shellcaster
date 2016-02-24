#!/usr/bin/env bash

# This is the client script for the broadcaster.
# It uses the openssl command to start an openssl connection with the server.
# Then it just pipes the information coming from the server to bash.
# If openssl dies/disconnects, then we just retry ad infinitum
ROOT_CA_FILE="./rootCA.pem"
case $# in
    0)
        echo "Need HOST:PORT as first argument"
        exit 1
        ;;
    1)
        HOST=$1
        ;;
    *)
        HOST=$1
        ROOT_CA_FILE=$1
        ;;
esac

# We will be using named FIFOs to talk with bash. Based on:
# http://unix.stackexchange.com/questions/29851/shell-script-mktemp-whats-the-best-method-to-create-temporary-named-pipe
tmpdir=$(mktemp -d)
if ! mkfifo "$tmpdir/sin"
then
    echo "Strange thing happening? Can't write to tmp? Attacker spoofing fifo?"
    exit 1;
fi

function on_exit()
{
    echo "Cleaning up FIFOs and children"
    kill `jobs -p`
    rm -rf "$tmpdir"
    exit 0
}
trap 'on_exit' EXIT

# The condition in this loop is based on
# http://unix.stackexchange.com/questions/53641/how-to-make-bidirectional-pipe-between-two-programs

# -verify and -verify_return_error guarantee we fail the connection if server
# does not have validly signed certificate. There so no one can hijack our
# machines unless we allow it

while true
do
    openssl s_client -connect $HOST -quiet \
            -verify 0 -verify_return_error -CAfile $ROOT_CA_FILE \
            2> /dev/null < "$tmpdir/sin" | \
        bash > "$tmpdir/sin"
    # Retry every second
    # Assumes temporary internet shortage.
    echo "Retrying"
    sleep 1
done
