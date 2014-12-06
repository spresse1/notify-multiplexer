/*
	UnixDomainInput.c - manages creating a local unix domain socket which
	listens for incoming datagrams and passes them up to the main server
*/

#define _GNU_SOURCE // for srnlen

#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <fcntl.h>
#include <string.h>
#include <errno.h>
#include <stdio.h>
#include "logging.h"

/*
Attempts to create the socket that will be used.
name: The pathname of the socket to create

Returns:
Positive: socket file descriptor
-1: Name too long
*/
int createUnixSocket(char name[]) {
	int sockd = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0);
	LOG(LOG_DEBUG, "Created socket, id %i", sockd);
	if (sockd==-1) {
		handle_error(__FILE__, __func__, __LINE__,1);
	}
	//We'll use select/poll instead
	//if (!fcntl(sockd, O_ASYNC)) { // and O_NONBLOCK?
	//	handle_error(__FILE__, __func__, __LINE__,1);
	//}
	if (!fcntl(sockd, O_NONBLOCK)) {
		handle_error(__FILE__, __func__, __LINE__,1);
	}
	if (strnlen(name, 108)==108) {
		// Name too long
		return -1;
	}
	
	// Set up struct telling us where to bind
	struct sockaddr_un addr;
	addr.sun_family=AF_UNIX;
	strncpy(addr.sun_path,name,107);
	addr.sun_path[107]='\0';
	
	// Take the address
	if (-1==bind(sockd, (struct sockaddr*)&addr, sizeof(addr))) {
		handle_error(__FILE__, __func__, __LINE__,1);
	}
	LOG(LOG_DEBUG,"%i: bound to %s", sockd,
		name);
	//start listening for connections - we'll deal with acepting later
	if (-1==listen(sockd, SOMAXCONN)) {
		handle_error(__FILE__, __func__, __LINE__,1);
	}
	LOG(LOG_DEBUG,"%i: listening", sockd);
	return sockd;
}

/* Accept a new connection.  Returns:
>0: socket file descriptor
0: Socket would have blocked; discard result and try again later
-1: an error occured, see errno
*/
int unixHandleAccept(int sockfd) {
	struct sockaddr_un addr;
	socklen_t len;
	int newSock = accept(sockfd, (struct sockaddr *)&addr, &len);
	if (newSock!=-1) {
		LOG(LOG_INFO, "Accepted connection as %i", newSock);
	} else {
		//error case
		if (errno==EAGAIN || errno==EWOULDBLOCK) {
			return 0;
		}
		//this is a real error, log a warning
		LOG( LOG_ERROR, "accept() failed to open client's socket: %s",
			strerror(errno));
		return -1;
	}
	return newSock;
}

/*
	Shutdown a socket cleanly.
	Return values as in shutdown(2)
*/
int destroyUnixSocket(int sockfd) {
	int res = shutdown(sockfd, SHUT_RDWR);
	if (-1==res) {
		log_msg(__FILE__, __func__, __LINE__,LOG_WARNING,
			"Failed to shutdown socket");
	}
	return res;
}
