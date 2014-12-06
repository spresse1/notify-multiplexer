/*
	Sample client.  Used mostly to test systems.
*/

#define _XOPEN_SOURCE 700

#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <string.h>
#include <errno.h>
#include "Message.h"
#include "logging.h"

int main(int argc, char *argv[]) {
	struct message smessage;
	char *tag=NULL;
	char *message=NULL;
	size_t taglen=0;
	size_t msglen=0;
	
	int sockd = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0);
	if (sockd==-1) log_msg(__FILE__,__func__, __LINE__,LOG_CRITICAL,
		"Open socket failed: %s", strerror(errno));
	struct sockaddr_un addr;
	addr.sun_family=AF_UNIX;
	strncpy(addr.sun_path,"./notify-multiplexer.sock",107);
	addr.sun_path[107]='\0';
	
	if (connect(sockd, (struct sockaddr *)&addr, sizeof(struct sockaddr_un))) {
		log_msg(__FILE__,__func__, __LINE__,LOG_CRITICAL,"connect failed: %s",
			strerror(errno));
	}	
	
	for (;;) {
		printf("Tag: ");
		getline(&tag, &taglen, stdin);
		printf("Message: ");
		getline(&message, &msglen, stdin);
		
		smessage.tag = tag;
		smessage.message = message;
		
		//allocate send buffer
		void *buf = calloc(1,1);
	
		int length = pack_message(buf, &smessage);
		log_msg(__FILE__,__func__, __LINE__,LOG_DEBUG,"Msg length is: %i",
			length);
		
		if (!send(sockd, buf, length, 0)) {
			log_msg(__FILE__,__func__, __LINE__,LOG_CRITICAL,"Send failed: %s",
				strerror(errno));
		}
		
		free(buf);
		smessage.tag=NULL;
		smessage.message=NULL;
	}
	
	free(tag);
	free(message);

}
