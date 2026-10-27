#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <sys/types.h>
#include <sys/wait.h>

struct shared {
    char sel[100];
    int b;
};

int main() {
    key_t key = ftok("shmfile",65);
    int shmid = shmget(key, sizeof(struct shared), 0666|IPC_CREAT);
    struct shared *shm = (struct shared*) shmat(shmid,(void*)0,0);

    int fd[2]; // pipe
    pipe(fd);

    printf("Provide Your Input From Given Options:\n");
    printf("1. Type a to Add Money\n");
    printf("2. Type w to Withdraw Money\n");
    printf("3. Type c to Check Balance\n");

    char choice;
    scanf(" %c",&choice);
    shm->sel[0] = choice;
    shm->sel[1] = '\0';
    shm->b = 1000;

    printf("Your selection: %c\n\n", choice);

    pid_t pid = fork();
    if(pid == 0) {
        // child process opr
        if(strcmp(shm->sel,"a") == 0){
            int amount;
            printf("Enter amount to be added:\n");
            scanf("%d",&amount);
            if(amount > 0){
                shm->b += amount;
                printf("Balance added successfully\n");
                printf("Updated balance after addition:\n%d\n", shm->b);
            } else {
                printf("Adding failed, Invalid amount\n");
            }
        }
        else if(strcmp(shm->sel,"w") == 0){
            int amount;
            printf("Enter amount to be withdrawn:\n");
            scanf("%d",&amount);
            if(amount > 0 && amount < shm->b){
                shm->b -= amount;
                printf("Balance withdrawn successfully\n");
                printf("Updated balance after withdrawal:\n%d\n", shm->b);
            } else {
                printf("Withdrawal failed, Invalid amount\n");
            }
        }
        else if(strcmp(shm->sel,"c") == 0){
            printf("Your current balance is:\n%d\n", shm->b);
        }
        else{
            printf("Invalid selection\n");
        }
        char msg[]="Thank you for using";
        write(fd[1], msg, strlen(msg)+1);
        close(fd[1]);
        shmdt(shm);
        exit(0);
    }
    else {
        wait(NULL);
        char buffer[100];
        read(fd[0], buffer, sizeof(buffer));
        printf("%s\n", buffer);
        close(fd[0]);
        shmdt(shm);
        shmctl(shmid, IPC_RMID, NULL);
    }
    return 0;
}
