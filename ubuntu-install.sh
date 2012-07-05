#!/bin/bash

function usage {
	echo ""
	echo "Notify client daemon installer"
	echo "./ubuntu-install.sh clientInstallDir [libraryInstallDir]"
}

if [ -z "$1" ]
then
	echo "The first argument must be a directory to install the client in"
	usage
	exit 1
fi

cp ubuntu-client.py "$1/notify-multiplex-clientd"

LIBDIR=""
if [ -z "$2" ]
then
	LIBDIR="/usr/local/lib/python2.7/dist-packages"
else
	LIBDIR="$2"
fi

#mkdir -p libnotifymultiplex
cp -r libnotifymultiplex "$LIBDIR/"
