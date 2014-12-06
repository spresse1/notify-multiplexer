/*
	Main server file.  This takes care of reading high level config, initalizing
	interfaces, and passing data from inputs to the network bus and from the bus
	to outputs.
	Note that messages sent locally are also sent to local outputs, skipping the
	bus entirely.
*/

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <sys/select.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>
#include <stdarg.h> // For logging
#include "logging.h"
#include "unixDomain.h"
#include "message.h"

#define DEFAULT_SERVER_SOCK	"./notify-multiplexer.sock"

int main(int argc, char* argv[]) {
	// blah blah blah option parsing
	
	// setup
	int unixSocket=createUnixSocket(DEFAULT_SERVER_SOCK);
	
	// select modifies the fd_sets, so we'll keep these as 'canonical'
	fd_set readfds;
	fd_set writefds; //Need?
	fd_set exceptfds; //pretty much everything
	FD_ZERO(&readfds);
	FD_ZERO(&writefds);
	FD_ZERO(&exceptfds);
	FD_SET(unixSocket, &readfds);
	FD_SET(unixSocket, &exceptfds);
	int maxfd=unixSocket+1; //to start, no other sockets
	
	//this will have to change to be able to handle signals and clean exits
	for (;;) {
		// Copy fd values for this loop
		fd_set readablefds;
		memcpy(&readablefds, &readfds, sizeof(fd_set));
		fd_set writeablefds;
		memcpy(&writeablefds, &writefds, sizeof(fd_set));
		fd_set exceptedfds;
		memcpy(&exceptedfds, &exceptfds, sizeof(fd_set));
		
		//actually do the select
		//TODO: change this to pselect with signals, when we start to deal with
		// signals
		LOG(LOG_DEBUG,"About to select...");
		select(maxfd, &readablefds, &writeablefds, &exceptedfds, NULL);
		LOG(LOG_DEBUG, "Done select");
		
		// Now go through and look at the available fds to see what needs doing
		for (int i=0; i<maxfd; i++) {
			if (FD_ISSET(i, &readablefds)) {
				if (i==unixSocket) {
					int newfd = unixHandleAccept(i);
					if (newfd>0) {
						FD_SET(newfd,&readfds);
						FD_SET(newfd,&exceptfds);
						if (newfd>=maxfd) maxfd=newfd+1;
						LOG(LOG_DEBUG,"Handle %i added to select.",newfd);
					} else {
						LOG(LOG_WARNING, 
							"Got bad handle back form unixHandleAccept()");
					}
				} else {
					// is a general socket, read and display
					//first, find out how big the message is
					char *buf = NULL;
					int msgsize = recv(i, buf, 0,
						MSG_PEEK | MSG_TRUNC | MSG_DONTWAIT);
					// check that we didn't error
					if (msgsize==-1) {
						if (errno==EAGAIN || errno==EWOULDBLOCK) {
							//log information that this isn't working right
							LOG(LOG_NOTICE,
								"Socket %d misbehaving (would block); terminating: %s", 
								i,strerror(errno));
						} else {
							// its a real error; different message, level
							LOG(LOG_WARNING,
								"Socket %d has critical error; terminating (%s)",
								i, strerror(errno));
						}
						FD_CLR(i,&readfds);
						FD_CLR(i,&exceptfds);
						destroyUnixSocket(i);
						
						// And pretend nothing happened
						continue;
					}
					
					//Allocate the correctly sized buffer
					buf = calloc(1,msgsize+1);
					// and repeat, but with trying to read the right size
					msgsize = recv(i, buf, msgsize, MSG_DONTWAIT);
					// check that we didn't error
					if (msgsize==-1) {
						if (errno==EAGAIN || errno==EWOULDBLOCK) {
							//log information that this isn't working right
							LOG(LOG_NOTICE,
								"Socket %d misbehaving (would block); terminating: %s", 
								i,strerror(errno));
						} else {
							// its a real error; different message, level
							LOG(LOG_WARNING,
								"Socket %d has critical error; terminating (%s)",
								i, strerror(errno));
						}
						FD_CLR(i,&readfds);
						FD_CLR(i,&exceptfds);
						destroyUnixSocket(i);
						
						// And pretend nothing happened
						continue;
					}
					buf[msgsize]='\0'; //force trailing null byte
						// (This is paranoia, since turning the buffer into 
						// a struct message promises it ends in a null byte in
						// the right places anyway)
					
					struct message *message_out = calloc(
						sizeof(struct message), 1);
					
					unpack_message(buf,msgsize, message_out);
					printf("Tag: %s\nMessage:%s\n", message_out->tag, 
						message_out->message);
					
					free(buf);
					free(message_out->tag);
					free(message_out->message);
				}
			}
			if (FD_ISSET(i, &writeablefds)) {
				//do something?
			}
			if (FD_ISSET(i, &exceptedfds)) {
				if (i==unixSocket) {
					FD_CLR(unixSocket, &readfds);
					FD_CLR(unixSocket, &exceptfds);
					destroyUnixSocket(unixSocket);
					unixSocket=createUnixSocket(DEFAULT_SERVER_SOCK);
					FD_SET(unixSocket, &readfds);
					FD_SET(unixSocket, &exceptfds);
					if ( unixSocket >= maxfd) {
						maxfd = unixSocket+1;
					}
				} else {
					FD_CLR(i, &readfds);
					FD_CLR(i, &exceptfds);
					destroyUnixSocket(i);
				}
			}
		}
	}
	return 0;
}
