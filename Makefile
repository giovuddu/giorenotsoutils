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

IMAGE     = giore-tests:bookworm
CONTAINER = giore-tests-dev
ARGS ?=
RUN_OPTS  = -v "$(CURDIR)":/work -v /work/.venv -v /work/build -v /work/bin -w /work

test-docker-build:
	docker build -f Dockerfile.test -t $(IMAGE) .

test: test-docker-build
	@docker start $(CONTAINER) >/dev/null 2>&1 || \
		docker run -d --name $(CONTAINER) $(RUN_OPTS) $(IMAGE) sleep infinity >/dev/null
	@TTY=$$([ -t 1 ] && echo -t); \
	docker exec -e ARGS="$(ARGS)" -i $$TTY $(CONTAINER) \
		sh -c 'make && uv run pytest $${ARGS:-tests/ -v}'

test-up: test-docker-build
	@docker start $(CONTAINER) >/dev/null 2>&1 || \
		docker run -d --name $(CONTAINER) $(RUN_OPTS) $(IMAGE) sleep infinity

test-shell: test-up
	docker exec -it $(CONTAINER) bash

test-down:
	-docker rm -f $(CONTAINER)

test-docker: test-docker-build
	docker run --rm $(RUN_OPTS) -e ARGS="$(ARGS)" $(IMAGE) \
		sh -c 'make && uv run pytest $${ARGS:-tests/ -v}'

.PHONY: test-docker-build test test-up test-shell test-down test-docker
