#!/usr/bin/env bash
# Following guide in:
# http://datacenteroverlords.com/2012/03/01/creating-your-own-ssl-certificate-authority/

# Store everything in the confidential directory
if [ ! -d ./confidential ]
then
   mkdir confidential || exit 1
fi
cd confidential

# Generate CA key
openssl genrsa -out rootCA.key 4096
# Generate CA certificate
echo "Please insert information for your Certificate Authority"
openssl req -x509 -new -nodes -key rootCA.key -sha512 -out rootCA.pem
# Put the root CA on the parent of this directory as well
cp rootCA.pem ../

# Generate server key
openssl genrsa -out server.key 4096
# Generate server certificate signing request
echo "Please insert information for your Server Certificate"
openssl req -new -key server.key -out server.csr

# Sign server certfiicate
openssl x509 -req -in server.csr -CA rootCA.pem -CAkey rootCA.key -CAcreateserial -out server.crt -sha512

# Archive and encrypt the archive
cd ../
tar -cvJf confidential.tar.xz confidential
echo "You will be asked to enter a passphrase to encrypt your certificates with"
gpg -o confidential.tar.xz.enc --cipher-algo AES256 --symmetric confidential.tar.xz
rm confidential.tar.xz
