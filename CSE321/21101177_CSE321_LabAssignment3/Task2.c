// task2.c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/msg.h>
#include <sys/types.h>
#include <sys/wait.h>

struct msg {
    long int type;
    char txt[100];
};

int main() {
    key_t key = ftok("msgqueue", 65);
    int msgid = msgget(key, 0666 | IPC_CREAT);

    char workspace[100];
    printf("Please enter the workspace name:\n");
    scanf("%s", workspace);

    if(strcmp(workspace,"cse321") != 0){
        printf("Invalid workspace name\n");
        msgctl(msgid, IPC_RMID, NULL);
        return 0;
    }

    struct msg message;
    message.type = 1;
    strcpy(message.txt, workspace);
    msgsnd(msgid, &message, sizeof(message.txt), 0);
    printf("Workspace name sent to otp generator from log in: %s\n\n", workspace);

    pid_t pid = fork();
    if(pid == 0){
        // OTP Generator
        msgrcv(msgid, &message, sizeof(message.txt), 1, 0);
        printf("OTP generator received workspace name from log in: %s\n\n", message.txt);

        int otp = getpid();
        sprintf(message.txt, "%d", otp);

        message.type = 2;
        msgsnd(msgid, &message, sizeof(message.txt), 0);
        printf("OTP sent to log in from OTP generator: %s\n", message.txt);

        message.type = 3;
        msgsnd(msgid, &message, sizeof(message.txt), 0);
        printf("OTP sent to mail from OTP generator: %s\n\n", message.txt);

        pid_t pid2 = fork();
        if(pid2 == 0){
            // Mail process
            msgrcv(msgid, &message, sizeof(message.txt), 3, 0);
            printf("Mail received OTP from OTP generator: %s\n", message.txt);

            message.type = 4;
            msgsnd(msgid, &message, sizeof(message.txt), 0);
            printf("OTP sent to log in from mail: %s\n", message.txt);

            exit(0);
        } else {
            wait(NULL);
            exit(0);
        }
    }
    else {
        wait(NULL);

        struct msg recvmsg1, recvmsg2;
        msgrcv(msgid, &recvmsg1, sizeof(recvmsg1.txt), 2, 0);
        printf("Log in received OTP from OTP generator: %s\n", recvmsg1.txt);

        msgrcv(msgid, &recvmsg2, sizeof(recvmsg2.txt), 4, 0);
        printf("Log in received OTP from mail: %s\n", recvmsg2.txt);

        if(strcmp(recvmsg1.txt, recvmsg2.txt) == 0){
            printf("OTP Verified\n");
        } else {
            printf("OTP Incorrect\n");
        }

        msgctl(msgid, IPC_RMID, NULL);
    }
    return 0;
}
