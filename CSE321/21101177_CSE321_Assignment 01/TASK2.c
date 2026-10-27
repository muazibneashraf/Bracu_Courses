#include <stdio.h>
#include <unistd.h>
#include <sys/wait.h>
#include <stdlib.h>

int main(void) {
    pid_t child = fork();
    if (child < 0) {
        perror("fork");
        return 1;
    }

    if (child == 0) {
        // Inside child
        pid_t grand = fork();
        if (grand < 0) {
            perror("fork");
            _exit(1);
        }
        if (grand == 0) {
            // Inside grandchild
            puts("I am grandchild");
            _exit(0);
        }
        // Child waits for grandchild
        waitpid(grand, NULL, 0);
        puts("I am child");
        _exit(0);
    }

    // Parent waits for child
    waitpid(child, NULL, 0);
    puts("I am parent");
    return 0;
}

