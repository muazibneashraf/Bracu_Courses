#include <stdio.h>
#include <stdlib.h>

static int cmp_desc(const void *a, const void *b) {

    int x = *(const int *)a;

    int y = *(const int *)b;

    return (y - x);

}

int main(int argc, char *argv[]) {

    if (argc < 2) {

        fprintf(stderr, "Usage: %s <int1> <int2> ...\n", argv[0]);

        return 1;

    }

    int n = argc - 1;

    int *arr = malloc(n * sizeof(int));

    if (!arr) { perror("malloc"); return 1; }

    for (int i = 0; i < n; ++i) arr[i] = atoi(argv[i+1]);

    qsort(arr, n, sizeof(int), cmp_desc);

    for (int i = 0; i < n; ++i) {

        if (i) printf(" ");

        printf("%d", arr[i]);

    }

    printf("\n");

    free(arr);

    return 0;

}