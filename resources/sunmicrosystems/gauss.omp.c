/* Gaussian elimination without pivoting.  */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/types.h>
#include <sys/times.h>
#include <sys/time.h>
#include <limits.h>
#include <omp.h>

#define MAXN 10000  /* Max value of N */
int N;  /* Matrix size */
int norm;
int procs;  /* Number of processors to use */

/* Matrices and vectors */
volatile float A[MAXN][MAXN], B[MAXN], X[MAXN];
/* A * X = B, solve for X */

/* Prototype */
void gauss();

/* returns a seed for srand based on the time */
unsigned int time_seed() {
    struct timeval t;
    struct timezone tzdummy;
    gettimeofday(&t, &tzdummy);
    return (unsigned int)(t.tv_usec);
}

/* Set the program parameters from the command-line arguments */
void parameters(int argc, char **argv) {
    int submit = 0;  /* = 1 if submission parameters should be used */
    int seed = 0;  /* Random seed */
    char uid[L_cuserid + 2]; /*User name */
    
    seed = time_seed();
    procs = omp_get_num_threads();

    /* Read command-line arguments */
    switch(argc) {
        case 4:
            {
                seed = atoi(argv[3]);
            } /* fall thru */
        case 3:
            {
                N = atoi(argv[2]);
                if (N < 1 || N > MAXN) {
                    printf("N = %i is out of range.\n", N);
                    exit(0);
                }
            }
        case 2:
            {
                procs = atoi(argv[1]);
            } break;
        default:
            {
                printf("Usage:\n");
                printf(" %s <num_processors> <matrix_dimension> [random seed]\n", argv[0]);
                printf(" %s submit\n", argv[0]);
                exit(0);
            }
    }
    omp_set_num_threads(procs);
    srand(seed);  /* Randomize */
    /* Print parameters */
    printf("Matrix dimension N = %i.\n", N);
    printf("Number of processors P = %i.\n", procs);
    printf("Random seed = %i\n", seed);
}

/* Initialize A and B (and X to 0.0s) */
void initialize_inputs() {
    int row, col;

    printf("\nInitializing...\n");
    for (col = 0; col < N; col++) {
        for (row = 0; row < N; row++) {
            A[row][col] = (float)rand() / 32768.0;
        }
        B[col] = (float)rand() / 32768.0;
        X[col] = 0.0;
    }

}

/* Print input matrices */
void print_inputs() {
    int row, col;

    if (N < 10) {
        printf("\nA =\n\t");
        for (row = 0; row < N; row++) {
            for (col = 0; col < N; col++) {
                printf("%5.2f%s", A[row][col], (col < N-1) ? ", " : ";\n\t");
            }
        }
        printf("\nB = [");
        for (col = 0; col < N; col++) {
            printf("%5.2f%s", B[col], (col < N-1) ? "; " : "]\n");
        }
    }
}

void print_X() {
    int row;

    if (N < 10) {
        printf("\nX = [");
        for (row = 0; row < N; row++) {
            printf("%5.2f%s", X[row], (row < N-1) ? "; " : "]\n");
        }
    }
}

void main(int argc, char **argv) {
    /* Timing variables */
    struct timeval etstart, etstop;  /* Elapsed times using gettimeofday() */
    struct timezone tzdummy;
    clock_t etstart2, etstop2;  /* Elapsed times using times() */
    unsigned long long usecstart, usecstop;
    struct tms cputstart, cputstop;  /* CPU times for my processes */

    /* Process program parameters */
    parameters(argc, argv);

    /* Initialize A and B */
    initialize_inputs();

    /* Print input matrices */
    print_inputs();

    /* Start Clock */
    printf("\nStarting clock.\n");
    gettimeofday(&etstart, &tzdummy);
    etstart2 = times(&cputstart);

    /* Gaussian Elimination */
    gauss();

    /* Stop Clock */
    gettimeofday(&etstop, &tzdummy);
    etstop2 = times(&cputstop);
    printf("Stopped clock.\n");
    usecstart = (unsigned long long)etstart.tv_sec * 1000000 + etstart.tv_usec;
    usecstop = (unsigned long long)etstop.tv_sec * 1000000 + etstop.tv_usec;

    /* Display output */
    print_X();

    /* Display timing results */
    printf("\nElapsed time = %g ms.\n",
            (float)(usecstop - usecstart)/(float)1000);
    printf("(CPU times are accurate to the nearest %g ms)\n",
            1.0/(float)CLK_TCK * 1000.0);
    printf("My total CPU time for parent = %g ms.\n",
            (float)( (cputstop.tms_utime + cputstop.tms_stime) -
                     (cputstart.tms_utime + cputstart.tms_stime) ) /
            (float)CLK_TCK * 1000);
    printf("My system CPU time for parent = %g ms.\n",
            (float)(cputstop.tms_stime - cputstart.tms_stime) /
            (float)CLK_TCK * 1000);
    printf("My total CPU time for child processes = %g ms.\n",
            (float)( (cputstop.tms_cutime + cputstop.tms_cstime) -
                     (cputstart.tms_cutime + cputstart.tms_cstime) ) /
            (float)CLK_TCK * 1000);
    printf("--------------------------------------------\n");

}

#define CHUNKSIZE 5
void gauss() {
    int row, col;  /* Normalization row, and zeroing
                    * element row and col */
    float multiplier;
    int tid = 0;

    /* Gaussian elimination */
    for (norm = 0; norm < N - 1; norm++) {
        #pragma omp parallel shared(A,B) private(multiplier,col, row)
        {
            #pragma omp for schedule(dynamic, CHUNKSIZE)
            for (row = norm + 1; row < N; row++) {
                multiplier = A[row][norm] / A[norm][norm];
                for (col = norm; col < N; col++) {
                    A[row][col] -= A[norm][col] * multiplier;
                }
                B[row] -= B[norm] * multiplier;
            }
        }
    }
    /* (Diagonal elements are not normalized to 1.  This is treated in back
     * substitution.)
     */

    /* Back substitution */
    for (row = N - 1; row >= 0; row--) {
        X[row] = B[row];
        for (col = N-1; col > row; col--) {
            X[row] -= A[row][col] * X[col];
        }
        X[row] /= A[row][row];
    }
}

