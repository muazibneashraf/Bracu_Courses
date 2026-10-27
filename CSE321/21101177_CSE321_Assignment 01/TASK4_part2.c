

#include <stdio.h>

#include <stdlib.h>

#include <unistd.h>

#include <sys/types.h>

#include <sys/wait.h>


static int cmp_desc(const void *a, const void *b) {

    int x = *(const int *)a;

    int y = *(const int *)b;

    return (y - x);

}


int main(int argc, char *argv[]) {

    int *arr = NULL;

    int n = 0;

    int builtin[] = {7, 2, 9, 4, 11, 6};


    if (argc > 1) {

        n = argc - 1;

        arr = malloc(n * sizeof(int));

        if (!arr) { perror("malloc"); return 1; }

        for (int i = 0; i < n; ++i) arr[i] = atoi(argv[i+1]);

    } else {

        arr = builtin;

        n = sizeof(builtin)/sizeof(builtin[0]);

    }


    int pipefd[2];

    if (pipe(pipefd) == -1) {

        perror("pipe");

        if (argc > 1) free(arr);

        return 1;

    }


    pid_t pid = fork();

    if (pid < 0) {

        perror("fork");

        if (argc > 1) free(arr);

        return 1;

    }


    if (pid == 0) {

        // Child: sort then send to parent

        close(pipefd[0]);

        qsort(arr, n, sizeof(int), cmp_desc);

        if (write(pipefd[1], arr, n * sizeof(int)) != (ssize_t)(n * sizeof(int))) {

            perror("write");

            close(pipefd[1]);

            if (argc > 1) free(arr);

            _exit(1);

        }

        close(pipefd[1]);

        if (argc > 1) free(arr);

        _exit(0);

    } else {

        // Parent: receive sorted array and print odd/even

        close(pipefd[1]);

        int *recv = malloc(n * sizeof(int));

        if (!recv) { perror("malloc"); close(pipefd[0]); if (argc > 1) free(arr); return 1; }

        ssize_t need = n * sizeof(int), got = 0;

        while (got < need) {

            ssize_t r = read(pipefd[0], ((char*)recv) + got, need - got);

            if (r < 0) { perror("read"); free(recv); close(pipefd[0]); if (argc > 1) free(arr); return 1; }

            if (r == 0) break;

            got += r;

        }

        close(pipefd[0]);

        waitpid(pid, NULL, 0);


        if (got == need) {

            printf("Sorted (desc):");

            for (int i = 0; i < n; ++i) printf(" %d", recv[i]);

            printf("\n");

            for (int i = 0; i < n; ++i)

                printf("%d -> %s\n", recv[i], (recv[i] % 2 == 0) ? "even" : "odd");

        } else {

            fprintf(stderr, "Did not receive full data from child.\n");

        }


        free(recv);

        if (argc > 1) free(arr);

    }

    return 0;

}



