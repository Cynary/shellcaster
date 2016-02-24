#!/usr/bin/env bash

# This is the client script for the broadcaster.
# It uses the openssl command to start an openssl connection with the server.
# Then it just pipes the information coming from the server to bash.
# If openssl dies/disconnects, then we just retry ad infinitum
ROOT_CA_FILE="rootCA.pem"

# We will be using named FIFOs to talk with bash. Based on:
# http://unix.stackexchange.com/questions/29851/shell-script-mktemp-whats-the-best-method-to-create-temporary-named-pipe
tmpdir=$(mktemp -d)
if ! mkfifo "$tmpdir/server_in" "$tmpdir/server_out"
then
    echo "Attacker?"
    exit 1;
fi

function on_exit()
{
    echo "Cleaning up FIFOs and background processes"
    rm -rf "$tmpdir"
    for j in `jobs -p`
    do
        kill $j
    done
}
trap 'on_exit' EXIT


# The condition in this loop is based on
# http://unix.stackexchange.com/questions/53641/how-to-make-bidirectional-pipe-between-two-programs

# -verify and -verify_return_error guarantee we fail the connection if server
# does not have validly signed certificate. There so no one can hijack our
# machines unless we allow it
while ! (
        openssl s_client -connect sicp-s4.mit.edu:6601 -quiet \
                -verify 0 -verify_return_error -CAfile $ROOT_CA_FILE \
                2> /dev/null > "$tmpdir/server_in" < "$tmpdir/server_out" & \
        bash > "$tmpdir/server_out" < "$tmpdir/server_in" & \
        exec 30<"$tmpdir/server_in" 31<"$tmpdir/server_out"; \
        false
    )
do
    # Retry every second
    # Assumes temporary internet shortage.
    echo "Retrying"
    sleep 1
done
