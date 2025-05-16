CC = gcc
FLAGS = -Wall -Wconversion -Wextra -pedantic -ggdb -Wno-unused-variable


SRC = main.c allocator.c block.c kernel.c tester.c ./avl/avl.c

.PHONY: run clean

run: main
	./main

main: $(SRC)
	$(CC) $(CFLAGS) -o main $(SRC)

clean:
	rm -rf ./main
