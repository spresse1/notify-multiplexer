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

function makeCACert {
    echo "
    We are about to generate you a CA certificate.  This is the root certificate used so your clients trust your server and vice-versa.
    If youve already seen this, there are two possibilities:
    1) You generated a CA certificate on this machine, but used the -c option to this script to name is something non-default.  Please remember to pass the name you used in -c every time you run this script
    2) You generated a CA certificate on another machine and are trying to generate a new client certificate for this machine.  If this is the case, you'll need to generate the client certificates on the machine where you have the CA certificate.
    If either of these applies to you, you probably don't want to be doing this.
    "
    read -ep "Are you sure you want to do this? [y/N]: " CHOICE
    
    if [ `expr match "$CHOICE" "y"` -eq  1 ]
    then
	PASSWORD=""
	while [ `expr length "$PASSWORD"` -lt 4 ]
	do
	    echo ""
	    read -esp "Password for the root certificate (will not echo, at least 4 characters): " PASSWORD
	done
	echo "" #print a newline after the passwd prompt
	#magic hack so we can specify the password on the command line.  Otherwise openssl tries to read it on stdin
	export PASSWD="$PASSWORD"
	read -ep "Name of your organization: [] " ORGNAME
	if [ -z "$ORGNAME" ]
	then
	    ORGNAME="."
	fi
	COMNAME=""
	while [ -z "$COMNAME" ]
	do
	    read -ep "Full length name for your root certificate.  This is probably the FQDN of your root domain (required): " COMNAME
	done
	echo "Generating your CA certificate:"
        openssl genrsa -des3 -passout env:PASSWD -out "$CACERTNAME.key" $BITS
	openssl req -new -x509 -passin env:PASSWD -days $DAYS -key "$CACERTNAME.key" -out "$CACERTNAME.crt" > /dev/null 2>&1 <<<".
.
.
$ORGNAME
.
$COMNAME
.
.
.
"
    else
	exit 0
    fi
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

#echo "Out dir is $OUTDIR"
#echo "CA cert is $CACERTNAME"
#echo "Bits are $BITS"
#echo "Days is $DAYS"

#exit 0

if [ `whoami` != "root" ]
then
    echo "******************************************
WARNING: OpenSSL requires root privaledges to run on some systems.  \
if this script fails, try rerunning it with root.
******************************************"
fi

cd "$OUTDIR"

if [ ! -f "$CACERTNAME.crt" ]
then
    makeCACert
fi

echo "Generating client certificate..."
read -ep "Name for this certificate: " CERTNAME
PASSWORD=""
    while [ `expr length "$PASSWORD"` -lt 4 ]
    do
	read -esp "Password for this certificate (will not echo): " PASSWORD
    done
#doesnt echo the newline, so add one ourseves
echo ""
echo "Now we're going to gather some basic info on who this certificate is for.  Most of it is irrelevent, but some you may want to set.  If a field is used, we explain what for."
read -ep "Name of your organization.  This is irrelevent, but useful if you ever want to query the certificate: [] " ORGNAME
if [ -z "$ORGNAME" ]
then
    ORGNAME="."
fi
read -ep "Name for your client: [] " CLINAME
if [ -z "CLINAME" ]
then
    CLINAME="."
fi
COMNAME=""
while [ -z "$COMNAME" ]
do
    read -ep "Full length name for your client.  This is probably the FQDN, if it has one. This is used by the notify-server to uniquely identify attached clients for e.g. allowing or denying access (required): " COMNAME
done
#magic hack so we can specify the password on the command line.  Otherwise openssl tries to read it on stdin
export PASSWD="$PASSWORD"
echo "We're now building a key. This could take a moment..."
openssl genrsa -des3 -passout env:PASSWD -out "$CERTNAME.key" $BITS
echo "Generating certificate signing request"
openssl req -new -passin env:PASSWD -key "$CERTNAME.key" -out "$CERTNAME.csr" > /dev/null 2>&1 <<<".
.
.
$ORGNAME
$CLINAME
$COMNAME
.
.
.
"
echo "
Generating final certificate.  You *will* be asked for the password for your ca certificate in this process
"
openssl x509 -req -days $DAYS -in "$CERTNAME.csr" -CA "$CACERTNAME.crt" \
    -CAkey "$CACERTNAME.key" -set_serial 01 -out "$CERTNAME.crt"

echo "Done! Enjoy!
Copy $CERTNAME.crt and $CERTNAME.key to whatever client they will be used on and configure them there."