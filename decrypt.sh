#!/usr/bin/env bash
# Use this script to remember how to decrypt the CA+cert container
# Based on the post:
# http://askubuntu.com/questions/27770/is-there-a-tool-to-encrypt-a-file-or-directory
# Originally encrypted with:
# gpg --symmetric < confidential.tar.xz > confidential.tar.xz.enc
gpg --decrypt < confidential.tar.xz.enc > confidential.tar.xz
