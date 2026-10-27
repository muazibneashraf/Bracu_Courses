#define _GNU_SOURCE
#include <stdio.h>
#include <unistd.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <stdlib.h>

int main(void) {
    // Shared memory for counter and root parent PID
    int *count = mmap(NULL, sizeof *count, PROT_READ | PROT_WRITE,
                      MAP_SHARED | MAP_ANONYMOUS, -1, 0);
    pid_t *rootpid = mmap(NULL, sizeof *rootpid, PROT_READ | PROT_WRITE,
                          MAP_SHARED | MAP_ANONYMOUS, -1, 0);

    if (count == MAP_FAILED || rootpid == MAP_FAILED) {
        perror("mmap");
        return 1;
    }

    *count = 0;
    *rootpid = getpid(); // store original parent's PID

    // Three forks as given in assignment
    pid_t a = fork(); if (a < 0) { perror("fork a"); return 1; }
    pid_t b = fork(); if (b < 0) { perror("fork b"); return 1; }
    pid_t c = fork(); if (c < 0) { perror("fork c"); return 1; }

    // Each process counts itself once
    __sync_fetch_and_add(count, 1);

    // If PID is odd, create one extra child
    if (getpid() % 2 == 1) {
        pid_t extra = fork();
        if (extra < 0) {
            perror("fork extra");
        } else if (extra == 0) {
            __sync_fetch_and_add(count, 1);
            _exit(0);
        }
    }

    // Reap all children for each process
    while (wait(NULL) > 0) { /* no-op */ }

    // Only original parent prints total
    if (getpid() == *rootpid) {
        printf("Total processes created (including original parent): %d\n", *count);
    }

    return 0;
}

