#include <stdio.h>
#include <stdlib.h>

int main(){

  printf("Original breaking point %x", sbrk(0));

  int *int_vec = (int*)malloc(10*sizeof(int));

  printf("Shifted to %x", sbrk(0));

  // "Initializing with 3
  memset((void*) int_vec, '3', sizeof (int) * 10);
  
  for (int i =0; i < 10; i++){
    printf("%c\n",(char)int_vec[i]);
  }
  
  printf("\n");
  
  // Filling in a loop
  for (int i =0; i < 10; i++){
    int_vec[i] = i*i + 2;
  }

  for (int i =0; i < 10; i++){
    printf("%d",int_vec[i]);
  }
  
  // Freeing
  free(int_vec);

  printf("Back to %x", sbrk(0));

  // printf("%d", sbrk(0));

  // void * ret = sbrk(4);

  // int *int_ptr = (int*)ret;
  // *int_ptr = 10;

  // printf("stored: %d",int_ptr); 
  // printf("stored: %d",*int_ptr); 
  
  // sbrk(-4);

  // printf("stored: %d",int_ptr);

  exit(0);
}