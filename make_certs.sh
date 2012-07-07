#!/bin/bash

#lets set some sane defaults
#where do we want to write out the files?  This is also where we look to tell
# if we already generated a CA cert
OUTDIR="/etc/notify-multiplexer"
# Default name of the CA cert file.  Note that we append .key for the private
# key and .crt for the public key.  No, I dont plan on letting you change these
CACERTNAME="ca"
# Default name of the server cert.  Note that we append .key for the private
# key and .crt for the public key.  No, I dont plan on letting you change these
SSLTLSCERT="server"
# How many days are out certs valid for?
DAYS="3650"
# How many bits in our keys?
BITS="4096"


#Set some reasonable error exit conditions
INVALIDARG=1

OTHERFAILURE=255

function usage {
	echo "
make_certs.sh: The notify-multiplexer tool for certificate generation.
notify-multiplexer uses SSL/TLS certificates to authenticate clients.  This script is designed to help with that.  It will walk you through the generation of all the certificates required to use notify-multiplexer.
The first time you run this script, you'll be prompted to generate the CA certificate.  This is the root certificate for your notify-multiplexer use.  It comes in 2 parts: ca.crt and ca.key.  ca.crt will have to go on every client, so that they can authenticate the server.  ca.key is the private (signing) key.  You'll want to keep that secret.  It gets used to signify that the keys given to each client are valid.  If you lose control of it, you'll need to generate a new one and resign all your client certificates.
After that (and each subsequent time you run the script), you'll be prompted to generate client certificates.  (Yes, the server actually uses a client certificate).  These certificates are the ones you copy to client machines in order to allow them to connect.
The following options can be given on the command line to adjust the behavior of this script:
-o	What directory to write files to [default: /etc/notify-multiplexer]
-c	CA cert name.  Note this is only the part that appears before the
	.key or .crt part! [default: ca]
-d	How many days the certificates are valid for [default: 3650]
-b	How many bits to put in the certificate [default: 4096]
-h	This help.
	"
	exit 0
}

#Now, lets do some fancy bash getopt-ing
# src: http://wiki.bash-hackers.org/howto/getopts_tutorial
# -o OUTDIR
# -c CA cert name
# -d days
# -b bits
while getopts ":ho:c:s:b:d:" OPT
do
	case $OPT in
	h)
		usage
		;;
	o)
		#outdir
		OUTDIR=$OPTARG
		;;
	c)
		#ca cert name
		CACERTNAME=$OPTARG
		;;
	b)
		#bits
		BITS=$OPTARG
		;;
	d)
		#days valid
		DAYS=$OPTARG
		;;
	\?)
		echo "Invalid options: -$OPTARG" >&2
		exit $INVALIDARG
		;;
	:)
		echo "Option -$OPTARG requires an argument, please see -h for help." >&2
		exit $INVALIDARG
		;;
	esac
done

echo "Out dir is $OUTDIR"
echo "CA cert is $CACERTNAME"
echo "Bits are $BITS"
echo "Days is $DAYS"

exit 0
openssl genrsa -des3 -out ca.key 4096
openssl req -new -x509 -days 3650 -key ca.key -out ca.crt
openssl genrsa -des3 -out server.key 4096
openssl req -new -key server.key -out server.csr
openssl x509 -req -days 3650 -in server.csr -CA ca.crt -CAkey ca.key -set_serial 01 -out server.crt
