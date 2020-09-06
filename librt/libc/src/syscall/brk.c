 #include <stdlib.h>

static void *_curbrk = NULL;

void * brk(void *addr){
    long res = syscall(12, (long) addr, 0, 0);
    return (void*)res;
}

void *sbrk(long incr){
  if (_curbrk == NULL)
    _curbrk = brk(0);

  if (incr == 0)
    return _curbrk;

  void* new_addr = _curbrk + incr;

  void *next_brk = brk(new_addr);

  if (next_brk < 0)
    return NULL;

  void *oldbrk = _curbrk;
  _curbrk = next_brk;

	return oldbrk;
}