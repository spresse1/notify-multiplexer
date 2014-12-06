/*
	Exported structs and function declarations from a UnixDomainSocket
*/

#ifndef UNIXDOMAININPUT_H
#define UNIXDOMAININPUT_H

int createUnixSocket(char name[]);

int destroyUnixSocket(int sockfd);

int unixHandleAccept(int sockfd);

#endif
