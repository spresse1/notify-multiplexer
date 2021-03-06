CFLAGS=-std=c99 -pedantic -Wall -Wextra -O -g
CXXFlLAGS=${CFLAGS}

SOURCES := $(wildcard *.c)
INCLUDE := $(wildcard *.h)
OBJECTS := message.o unixDomain.o logging.o

all: server client

server: server.o $(OBJECTS)

client: client.o $(OBJECTS)

$(OBJECTS): $(SOURCES) $(INCLUDE)

clean:
	rm -rf *.o server client
