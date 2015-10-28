#include "mpi.h"
#include <stdio.h>
#include <stdlib.h>
#include <malloc.h>
// mpicc -o sc scattermatrix.c && /usr/lib/mpich-mpd/bin/mpirun -np 4 ./sc
 
#define MAXN 10
 
void print_row(char* name, int* R,int i, int N, int rank) {
    int j;
    printf("@[%d] (%s): ", rank, name);
    for(j=0; j<N; j++) printf ("%d,",R[ i * N + j]);
    printf("\n");
}

int check(int v, char* err) {
    if (v != MPI_SUCCESS) {
        fprintf(stderr,"err: @%s\n", err);
        fprintf(stderr,"----------------------------\n");
        fflush(stdout);
        MPI_Finalize();
        exit(-1);
    } else {
        printf("pass:%s\n", err);
    }
}

int main( int argc, char **argv ) {
    int rank, size, i,j, r;
    //int table[MAXN][MAXN];
    int newtable[MAXN * MAXN];
    int row[MAXN];
    int ranks[MAXN];
    int last;
    int v;
    int N = 5;

    MPI_Datatype subarray;

    int array_size[] ={N};
    int array_subsize[] = {N};
    int array_start[] = {0};

    MPI_Comm  COMM_LAST;
    MPI_Group group_world, group_last;

    MPI_Init( &argc, &argv );
    MPI_Comm_rank( MPI_COMM_WORLD, &rank );
    MPI_Comm_size( MPI_COMM_WORLD, &size );

    MPI_Type_create_subarray(1, array_size, array_subsize, array_start, MPI_ORDER_C, MPI_INT, &subarray);
    MPI_Type_commit(&subarray);

    last = N % size;

    /* If I'm the root (process 0), then fill out the big table */
    if (rank == 0) {
        int k = 0;
        for ( i=0; i<N; i++) 
            for ( j=0; j<N; j++ ) 
                newtable[i*N + j] = ++k;
    } else {
        for ( i=0; i<N; i++)  {
            for ( j=0; j<N; j++ ) 
                newtable[i * N + j] = 0;
            row[i] = 0;
        }
    }
    printf("@[%d] Initialize..\n", rank);
    MPI_Barrier(MPI_COMM_WORLD);
 
    for(r = 0; r < size; r++) {
        MPI_Barrier(MPI_COMM_WORLD);
        if(rank == r) {
            printf("@[%d] X-> \n", rank);
            for(i=0; i<N; i++)
                print_row("Xnewtable",newtable,i, N, rank);
        }
        MPI_Barrier(MPI_COMM_WORLD);
    }

/*    if(!rank)
        for(i=0; i<N; i++)
            print_row("newtable", newtable,i, N, rank);*/

    for(i=0; i <last; i++) ranks[i] = i;

    MPI_Comm_group(MPI_COMM_WORLD, &group_world);
    MPI_Group_incl(group_world, last, ranks, &group_last);
    MPI_Comm_create(MPI_COMM_WORLD, group_last, &COMM_LAST);

    for(i = 0; i < N; i+= size ) {
        if(!rank)printf("scatter <%d>\n", i);
        if (i < (N - last)) {
            MPI_Scatter(
                    &newtable[i * N + 0], 1, subarray,
                    &newtable[(i + rank) * N + 0], 1, subarray,
                    0,MPI_COMM_WORLD);
        } else {
            if (rank < last) {
                MPI_Scatter(
                        &newtable[i * N + 0], 1, subarray,
                        &newtable[ (i + rank) * N + 0], 1, subarray,
                        0, COMM_LAST);
            }
        }
    }
    MPI_Barrier(MPI_COMM_WORLD);
    
    for(r = 0; r < size; r++) {
        MPI_Barrier(MPI_COMM_WORLD);
        if(rank == r) {
            printf("@[%d] -> \n", rank);
            for(i=0; i<N; i++)
                print_row("Xnewtable",newtable,i, N, rank);
        }
        MPI_Barrier(MPI_COMM_WORLD);
    }

    MPI_Barrier(MPI_COMM_WORLD);
    printf("@[%d] ......\n", rank);
    MPI_Barrier(MPI_COMM_WORLD);

    // reset our little matrix
    if (rank == 0) {
        int k = 0;
        for ( i=0; i<N; i++) 
            for ( j=0; j<N; j++ ) 
                newtable[i * N  + j] = 0;
        for(r = 0; r < size; r++) {
            printf("@[%d]\n", rank);
            if(rank == r) {
                for(i=0; i<N; i++)
                    print_row("newtable",newtable, i, N, rank);
            }
        }
    }
    MPI_Barrier(MPI_COMM_WORLD);

    for(i = 0; i < N; i+= size ) {
        if(!rank)printf("gather <%d>\n", i);
        if (i < (N - last)) {
            MPI_Gather(
                    &newtable[ ( i + rank ) * N + 0], 1, subarray,
                    &newtable[i * N + 0], 1, subarray,
                    0, MPI_COMM_WORLD);
        } else {
            if (rank < last) {
                MPI_Gather(
                        &newtable[(i + rank) * N + 0], 1, subarray,
                        &newtable[i*N + 0], 1, subarray,
                        0,COMM_LAST);
            }
        }
    }
    if (rank == 0) {
        for(r = 0; r < size; r++) {
            printf("@[%d]\n", rank);
            if(rank == r) {
                for(i=0; i<N; i++)
                    print_row("newtable",newtable,i, N, rank);
            }
        }
    }

    MPI_Group_free(&group_last);
    if (rank < last) 
        MPI_Comm_free(&COMM_LAST);
    MPI_Finalize();
    return 0;
}
