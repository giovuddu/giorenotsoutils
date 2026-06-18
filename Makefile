CC = gcc
CFLAGS = -Wall -Wextra -Ilib

LIB_SRC = $(wildcard lib/*.c)
LIB_OBJ = $(patsubst lib/%.c,build/%.o,$(LIB_SRC))
SRC = $(wildcard src/*.c)
BIN = $(patsubst src/%.c,bin/%,$(SRC))

all: $(BIN)

bin/%: src/%.c $(LIB_OBJ) | bin
	$(CC) $(CFLAGS) -o $@ $< $(LIB_OBJ)

build/%.o: lib/%.c | build
	$(CC) $(CFLAGS) -c -o $@ $<

bin:
	mkdir -p bin

build:
	mkdir -p build

clean:
	rm -rf build $(BIN)

.PHONY: all clean
