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

# -- tests --
IMAGE = giore-tests:bookworm
ARGS ?=
RUN_OPTS = --rm \
	-v "$(CURDIR)":/work -v /work/.venv -v /work/build -v /work/bin \
	-w /work

test-docker-build:
	docker build -f Dockerfile.test -t $(IMAGE) .

test-docker: test-docker-build
	docker run $(RUN_OPTS) -e ARGS="$(ARGS)" $(IMAGE) \
		sh -c 'make && uv run pytest $${ARGS:-tests/ -v}'

test-docker-shell: test-docker-build
	docker run $(RUN_OPTS) -it $(IMAGE) bash

.PHONY: test-docker-build test-docker test-docker-shell
