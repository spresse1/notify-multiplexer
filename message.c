/* Message.c
	Handles most things about the basic message format common to all inputs and 
	outputs
	
	Binary buffer message format:
	uint16 - length of tag, including null byte
	uint32 - length of message, including null byte
	char * - tag, null terminated
	char * - message, null terminated
*/

#include <sys/types.h>
#include <string.h>
#include <stdlib.h>
#include <arpa/inet.h>
#include "Message.h"

/*
Calculates the correct size for the buffer to pass to pack_message
Inputs:
tag: null terminated string
message: null terminated string 
Output:
Integer length to pass to ?alloc()
*/
int calculate_message(const char *tag, const char *message) {
	return 8 + strlen(tag) + strlen(message);
}

/*
Convenience method for packing up messages.
buffer: The buffer to place the message into.  This will automatically be 
	realloc'd to the correct size.  Caller must still free it.
message: the struct representing the message
tag: the tag to use to identify the message
message: the text of the message to send
returns: length of buffer or -1 to indicate error
*/
int pack_message(void *buffer, const struct message *message) {
	//resize whatever buffer we were given
	int length = calculate_message(message->tag, message->message);
	int taglen = strlen(message->tag)+1;
	int msglen = strlen(message->message)+1;
	buffer = realloc(buffer, length);
	
	//pack things into it
	*(uint16_t *)buffer = htons(taglen);
	*((uint16_t *)buffer+1) = htons(msglen);
	memcpy((uint16_t *)buffer+2, message->tag, taglen);
	memcpy((char *)((uint16_t *)buffer+2)+taglen, message->message, msglen);
	
	return length;
}

/*
Unpacks a received buffer into a struct message.
buffer: the network-received buffer.
size: The size of buffer
message: an allocated struct message.  Note that all the char *s must have 
	memory allocated, though it need not be of any particular size.  This
	function will use realloc() to size them appropriately
Returns 0 on success
1 on invalid buffer.  Typically this means the lengths recorded for the tag and 
	message are longer than the size of the buffer.
*/
int unpack_message(const void *buffer, size_t size, struct message *message) {
	// Pull out the lengths to validity-check
	uint16_t taglen = ntohs(*(uint16_t *)buffer);
	uint16_t msglen = ntohs(*((uint16_t *)buffer+1));
	
	if (taglen+msglen > size) return 1; //If this is true, we'd read memory
		// from beyind the end of the buffer.
		// since this comes form the network, God only knows what's in it.
		// If we pass this, the message that comes back may be junk, but we
		// won't buffer overrun.
	
	//realloc buffers to be the right sizes
	message->tag = realloc(message->tag, taglen);
	message->message = realloc(message->message, msglen);
	
	// copy strings out of the buffer
	memcpy(message->tag, (uint16_t *)buffer + 2, taglen);
	memcpy(message->message, (char *)((uint16_t *)buffer + 2) + taglen, msglen);
	
	//force null bytes
	message->tag[taglen-1]='\0';
	message->message[msglen-1]='\0';
	
	return 0;
}
