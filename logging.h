/*
	server.h - universal includes
*/
#ifndef LOGGING_H
#define LOGGING_H

/*struct message {
	uint16 type;
	uint16 tagLen; //Length of the tag's string
	uint32 bodyLen; //Length of the body
	char[] tag; //The tag
	char[] body;
};*/

#define LOG_DEBUG		0
#define LOG_INFO		1
#define LOG_NOTICE		2
#define	LOG_WARNING		3
#define LOG_ERROR		4
#define	LOG_CRITICAL	5

void handle_error(const char *file, const char *func, int line, int status);
int log_msg(const char *file, const char *func, int line, int level, 
	const char *format, ...); 
#endif
