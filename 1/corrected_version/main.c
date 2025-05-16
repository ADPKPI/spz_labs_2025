#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "tree.h"
#include "allocator.h"
#include "tester.h"
#include "block.h"
#include "tree.h"
#include "avl/avl_impl.h"

static void * buffer_alloc_and_fill(size_t size)
{
    char *buf;
    size_t i;

    buf = mem_alloc(size);
    if (buf != NULL) {
        for (i = 0; i < size; ++i) {
            buf[i] = (char)rand();
        }
    }
    return buf;
}

int main(void)
{
	void *ptrA, *ptrB, *ptrC, *ptrD;
	ptrA = mem_alloc(50000);
	ptrB = mem_alloc(10);
	ptrC = mem_alloc(12000);
	ptrD = mem_alloc(1500);
	mem_show("allocs");
	ptrA = mem_realloc(ptrA, 100000);
	mem_show("realloc ptrA -> 100000");
	mem_free(ptrA);
	mem_show("free ptrA");
	mem_realloc(ptrD, 2000);
	mem_show("realloc ptrD -> 2000");

        // Запускаємо тестер (якщо не треба, то можна закоментувати наступні 2 рядки)
	// srand(time(NULL)); 
	// tester(true); 
}
