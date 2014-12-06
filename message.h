/*
Public interface to message packing and unpacking
*/

struct message {
	char *tag;
	char *message;
};

int unpack_message(const void *buffer, size_t size, struct message *message);
int pack_message(void *buffer, const struct message *message);
