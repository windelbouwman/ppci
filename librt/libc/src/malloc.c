// Code from https://github.com/arjun024/memalloc/pull/4

#include <stdlib.h>

struct header_t {
	size_t size;
	unsigned is_free;
	struct header_t *next;
};

struct header_t *head = NULL, *tail = NULL;


// from https://www.geeksforgeeks.org/write-memcpy/
void memmove(void *dest, void *src, size_t n) 
{ 
   char *csrc = (char *)src; 
   char *cdest = (char *)dest; 
  
   // Copy contents of src[] to dest[] 
   for (int i=0; i<n; i++) 
       cdest[i] = csrc[i];
} 

// from https://www.geeksforgeeks.org/write-memcpy/
void memcpy(void *dest, void *src, size_t n) 
{ 
   char *csrc = (char *)src; 
   char *cdest = (char *)dest; 
  
   for (int i=0; i<n; i++) 
       cdest[i] = csrc[i]; 
} 

// https://www.includehelp.com/c-programs/write-your-own-memset-function-in-c.aspx
void memset(void* str, char ch, size_t n){
	int i;

	//type cast the str from void* to char*
	char *s = (char*) str;

	//fill "n" elements/blocks with ch
	for(i=0; i<n; i++)
		s[i]=ch;
}

struct header_t *get_free_block(size_t size){
	struct header_t *curr = head;
	while(curr) {
		/* see if there's a free block that can accomodate requested size */
		if (curr->is_free && curr->size >= size)
			return curr;
		curr = curr->next;
	}
	return NULL;
}

// size_t release_size(){
// 	/* This calculates the size of all trailing elements */
// 	struct header_t *new_tail, *tmp;
// 	size_t release_size_ = 0;
// 	new_tail = tmp = head;

// 	while (tmp) {
// 		if(tmp->next == NULL) {
// 			new_tail->next = NULL;
// 			tail = new_tail;
// 		}
// 		if(!tmp->is_free) {
// 			new_tail = tmp;
// 			release_size_ = 0;
// 		} else {
// 			release_size_ -= tmp->size - sizeof(*tmp);
// 		}
// 		tmp = tmp->next;
// 	}
// 	/* Head equals tail can indicate two things:
// 	     * this is the last remaining element on the heap
// 	     * there are no remaining elements on the heap
// 	*/
// 	if (head == tail && head->is_free) {
// 		head = tail = NULL;
//     }

// 	return release_size_;
// }

void free(void *block){
	struct header_t *header, *tmp;
	/* program break is the end of the process's data segment */
	void *programbreak;

	if (!block)
		return;

	header = (struct header_t*)block - 1;
    
	/* sbrk(0) gives the current program break address */
	programbreak = sbrk(0);

	/*
	   Check if the block to be freed is the last one in the
	   linked list. If it is, then we could shrink the size of the
	   heap and release memory to OS. Else, we will keep the block
	   but mark it as free.
	 */
	if ((char*)block + header->size == programbreak) {
		/*
		   sbrk() with a negative argument decrements the program break.
		   So memory is released by the program to OS.
		*/
		// sbrk(release_size());

		if (head == tail)
			head = tail = NULL;
		else{
			tmp = head;

			while (tmp){
				if(tmp->next == tail) {
					tmp->next = NULL;
					tail = tmp;
				}
				tmp = tmp->next;
			}
		}
		sbrk(0 - sizeof(struct header_t) - header->size);
		return;
	}
	header->is_free = 1;
}

void *malloc(size_t size){
	size_t total_size;
	void *block;
	struct header_t *header;

	if (!size)
		return NULL;

	header = get_free_block(size);

	if (header) {
		/* Woah, found a free block to accomodate requested memory. */
		header->is_free = 0;
		return (void*)(header + 1);
	}
	
    /* We need to get memory to fit in the requested block and header from OS. */
	total_size = sizeof(struct header_t) + size;
	block = sbrk(total_size);
	if (block == NULL) {
		return NULL;
	}

	header = block;
	header->size = size;
	header->is_free = 0;
	header->next = NULL;

	if (!head)
		head = header;

	if (tail)
		tail->next = header;

	tail = header;
	return (void*)(header + 1);
}

void *calloc(size_t num, size_t nsize){
	size_t size;
	void *block;

	if (!num || !nsize)
		return NULL;

	size = num * nsize;
	/* check mul overflow */

	if (nsize != size / num)
		return NULL;

	block = malloc(size);

	if (!block)
		return NULL;

	memset(block, 0, size);
    
	return block;
}

void *realloc(void *block, size_t size){
	struct header_t *header;
	void *ret;

	if (!block || !size)
		return malloc(size);

	header = (struct header_t*)block - 1;

	if (header->size >= size)
		return block;

	ret = malloc(size);

	if (ret) {
		/* Relocate contents to the new bigger block */
		memcpy(ret, block, header->size);
		/* Free the old memory block */
		free(block);
	}
	return ret;
}