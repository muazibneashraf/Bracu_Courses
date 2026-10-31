#include <stdio.h>
#include <pthread.h>

int fib[41]; 

void *generate_fib(void *arg) {
    int n = *(int *)arg;
    fib[0] = 0;
    if (n > 0) fib[1] = 1;

    for (int i = 2; i <= n; i++) {
        fib[i] = fib[i - 1] + fib[i - 2];
    }
    return NULL;
}

void *search_fib(void *arg) {
    int *data = (int *)arg;
    int n = data[0];     
    int s = data[1];      
    int *queries = &data[2]; 

    for (int i = 0; i < s; i++) {
        int idx = queries[i];
        if (idx >= 0 && idx <= n)
            printf("result of search #%d = %d\n", i + 1, fib[idx]);
        else
            printf("result of search #%d = -1\n", i + 1);
    }
    return NULL;
}

int main() {
    int n, s;
    printf("Enter the term of fibonacci sequence (0-40): ");
    scanf("%d", &n);

    pthread_t t1, t2;
    pthread_create(&t1, NULL, generate_fib, &n);
    pthread_join(t1, NULL);

    for (int i = 0; i <= n; i++) {
        printf("a[%d] = %d\n", i, fib[i]);
    }

    printf("How many numbers are you willing to search?: ");
    scanf("%d", &s);
    int data[2 + s]; 

    data[0] = n;
    data[1] = s;

    for (int i = 0; i < s; i++) {
        printf("Enter search %d: ", i + 1);
        scanf("%d", &data[2 + i]);
    }

    pthread_create(&t2, NULL, search_fib, data);
    pthread_join(t2, NULL);

    return 0;
}

