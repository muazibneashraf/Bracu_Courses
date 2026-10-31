#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <semaphore.h>
#include <unistd.h>
#include <time.h>

#define NUM_STUDENTS 10
#define NUM_CHAIRS 3

typedef struct {
    sem_t sem;
    int id;
} StudentSem;

pthread_mutex_t chair_mutex = PTHREAD_MUTEX_INITIALIZER;
sem_t students_sem;
int chairs_available = NUM_CHAIRS;
StudentSem* student_queue[NUM_CHAIRS];
int queue_head = 0;
int queue_tail = 0;
int queue_size = 0;

int served_students = 0;
pthread_mutex_t served_mutex = PTHREAD_MUTEX_INITIALIZER;

void* student_thread(void* arg) {
    int id = *((int*)arg);
    free(arg);

    usleep(rand() % 1000000);

    pthread_mutex_lock(&chair_mutex);
    if (chairs_available > 0) {
        chairs_available--;
        queue_size++;

        StudentSem* student_sem_struct = malloc(sizeof(StudentSem));
        sem_init(&student_sem_struct->sem, 0, 0);
        student_sem_struct->id = id;

        student_queue[queue_tail] = student_sem_struct;
        queue_tail = (queue_tail + 1) % NUM_CHAIRS;

        printf("Student %d started waiting for consultation\n", id);
        pthread_mutex_unlock(&chair_mutex);

        sem_post(&students_sem);

        sem_wait(&student_sem_struct->sem);

        printf("Student %d is getting consultation\n", id);
        usleep(rand() % 1000000);

        printf("Student %d finished getting consultation and left\n", id);

        pthread_mutex_lock(&served_mutex);
        printf("Number of served students: %d\n", served_students);
        served_students++;
        pthread_mutex_unlock(&served_mutex);

        sem_destroy(&student_sem_struct->sem);
        free(student_sem_struct);
    } else {
        printf("No chairs remaining in lobby. Student %d Leaving.....\n", id);
        pthread_mutex_unlock(&chair_mutex);

        printf("Student %d finished getting consultation and left\n", id);
        pthread_mutex_lock(&served_mutex);
        printf("Number of served students: %d\n", served_students);
        pthread_mutex_unlock(&served_mutex);
    }
    return NULL;
}

void* st_thread(void* arg) {
    (void)arg;
    while (1) {
        sem_wait(&students_sem);

        pthread_mutex_lock(&chair_mutex);
        if (queue_size == 0) {
            pthread_mutex_unlock(&chair_mutex);
            continue;
        }

        StudentSem* student = student_queue[queue_head];
        queue_head = (queue_head + 1) % NUM_CHAIRS;
        queue_size--;
        chairs_available++;
        int current_queue_size = queue_size;
        pthread_mutex_unlock(&chair_mutex);

        sem_post(&student->sem);

        printf("A waiting student started getting consultation\n");
        printf("Number of students now waiting: %d\n", current_queue_size);
        printf("ST giving consultation\n");
    }
    return NULL;
}

int main() {
    srand(time(NULL));

    sem_init(&students_sem, 0, 0);

    pthread_t st_tid;
    pthread_create(&st_tid, NULL, st_thread, NULL);

    pthread_t student_threads[NUM_STUDENTS];
    for (int i = 0; i < NUM_STUDENTS; i++) {
        int* id = malloc(sizeof(int));
        *id = i;
        pthread_create(&student_threads[i], NULL, student_thread, id);
    }

    for (int i = 0; i < NUM_STUDENTS; i++) {
        pthread_join(student_threads[i], NULL);
    }

    pthread_cancel(st_tid);
    sem_destroy(&students_sem);
    pthread_mutex_destroy(&chair_mutex);
    pthread_mutex_destroy(&served_mutex);

    return 0;
}
