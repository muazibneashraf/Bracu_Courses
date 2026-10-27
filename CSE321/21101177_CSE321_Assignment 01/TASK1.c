#define _GNU_SOURCE
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/stat.h>

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        return 1;
    }

    int fd = open(argv[1], O_WRONLY | O_CREAT | O_APPEND, 0644);
    if (fd == -1) { perror("open"); return 1; }

    char line[1024];
    while (1) {
        printf("Enter text (type -1 to stop): ");
        fflush(stdout);
        if (!fgets(line, sizeof line, stdin)) break;

        size_t n = strlen(line);
        if (n && line[n-1] == '\n') line[n-1] = '\0';
        if (strcmp(line, "-1") == 0) break;

        line[n] = '\n';
        if (write(fd, line, strlen(line)) == -1) { perror("write"); break; }
    }
    close(fd);
    puts("Done.");
    return 0;
}
