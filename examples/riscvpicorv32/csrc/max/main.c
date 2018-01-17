#include <stdio.h>

int find_max(int *arr, int size)
{
  int res = 0, i;

  for (i = 0; i < size; i++)
    if (arr[i] > res)
      res = arr[i];

  return res;
}

void main_main()
{

  int max_elem;
  int arr[5];

  arr[0] = 5;
  arr[1] = 54;
  arr[2] = 1;
  arr[3] = 94;
  arr[4] = 12;

  max_elem = find_max(arr, 5);

  printf("%d\n",max_elem);


  while(1) {}
}