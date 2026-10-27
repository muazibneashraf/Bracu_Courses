#include <stdio.h>

#include <stdlib.h>

#include <sys/types.h>

#include <sys/wait.h>

#include <unistd.h>


int main(void) {

    pid_t child = fork();

    if (child < 0) { perror("fork"); return 1; }


    if (child == 0) {

        // In child: create 3 grandchildren

        for (int i = 0; i < 3; ++i) {

            pid_t g = fork();

            if (g < 0) { perror("fork"); _exit(1); }

            if (g == 0) {

                // grandchild

                printf("3. Grand Child process ID: %d\n", getpid());

                fflush(stdout);

                _exit(0);

            } else {

                // child waits each grandchild

                waitpid(g, NULL, 0);

            }

        }

        // Child prints its own ID once

        printf("2. Child process ID: %d\n", getpid());

        fflush(stdout);

        _exit(0);

    } else {

        // Parent

        waitpid(child, NULL, 0);

        printf("1. Parent process ID: %d\n", getpid());

        fflush(stdout);

    }

    return 0;

}
