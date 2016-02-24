#!/usr/bin/env bash
# Use this script to remember how to decrypt the CA+cert container
# Based on the post:
# http://askubuntu.com/questions/27770/is-there-a-tool-to-encrypt-a-file-or-directory
# Originally encrypted with:
# gpg --symmetric < confidential.tar.xz > confidential.tar.xz.enc
# Then I saw this post:
# http://superuser.com/questions/633715/how-do-i-fix-warning-message-was-not-integrity-protected-when-using-gpg-symme
# And I encrypted with:
# gpg -o confidential.tar.xz.enc --cipher-algo AES256 --symmetric confidential.tar.xz
gpg -o confidential.tar.xz --decrypt confidential.tar.xz.enc
