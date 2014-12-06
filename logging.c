/*
	Generic error handler used throughout.  Automatically uses errno to collect
	the error
	just call this as: handle_error(__FILE__, __func__, __LINE__, status)
	Status is the only value that should change - it is the code that exit will 
		be called with. 0 does not exit
*/

#include <stdlib.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <errno.h>
#include "logging.h"

void handle_error(const char *file, const char *func, int line, int status) {
	log_msg(file, func, line, LOG_CRITICAL, "Critical error: %s",
		strerror(errno));
	if (status) exit(status);
}

char *log_level_text[] = {
	"DEBUG",
	"INFO",
	"NOTICE",
	"WARNING",
	"ERROR",
	"CRITICAL"
};

/*
	Does the appropriate loggy stuff.
	The first three arguments are preprocessor macros: __FILE__, __func__, and
	__LINE__, respectively.
	level is one of the LOG_* constants
	The remaining arguments are as in printf(3) (which this function in fact 
	wraps).
	Returns: See printf(3).
*/
int log_msg(const char *file, const char *func, int line, int level, 
	const char *format, ...) {
	va_list args;
	va_start(args, format);
	// Need to modify the format to put our own logging info in front of the
	// format text
	int i=1;
	for (int linen=abs(line); linen>10; i++, linen/=10);
	
	char *mformat = calloc(
		strlen(file) + strlen(func) + 
			strlen(__DATE__) + strlen(__TIME__) +
			i + 2 //One character for every power of 10 and 1 for sign
			+ strlen(log_level_text[level]) +
			strlen(format) + 13, sizeof(char));
	sprintf(mformat, "[%s %s] %s:%s.%d %s %s\r\n", __DATE__, __TIME__, file, func,
		line, log_level_text[level],format);
	// Printf that takes variadic arguments list
	int ret = vprintf(mformat, args);
	free(mformat);
	va_end(args); //must be called
	return ret;
}
