/*
 * Copyright (c) 2014-2016 Jim Tremblay
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 */

#define NOS_PRIVATE
#include "nOS.h"

#ifdef __cplusplus
extern "C" {
#endif

#if (NOS_CONFIG_MEM_ENABLE > 0)
#if (NOS_CONFIG_MEM_SANITY_CHECK_ENABLE > 0)
/**********************************************************************************************************************
 *                                                                                                                    *
 * Name             : _SanityCheck                                                                                    *
 *                                                                                                                    *
 * Description      : Check if pointer is valid for given memory block (useful before freeing block).                 *
 *                                                                                                                    *
 * Parameters                                                                                                         *
 *   mem            : Pointer to mem object.                                                                          *
 *   block          : Pointer to previously allocated block.                                                          *
 *                                                                                                                    *
 * Return           : Error code.                                                                                     *
 *   NOS_OK         : Pointer is valid.                                                                               *
 *   NOS_E_INV_VAL  : Pointer to block is outside mem defined range.                                                  *
 *                      See note 1                                                                                    *
 *   NOS_E_OVERFLOW : Too much block has been freed or block is already free.                                         *
 *                      See note 1                                                                                    *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Never suppose to happen normally, can be a sign of corruption.                                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
static nOS_Error _SanityCheck (nOS_Mem *mem, void *block)
{
    nOS_Error   err;

    if (block < mem->buffer) {
        /* Memory block pointer is out of range. */
        err = NOS_E_INV_VAL;
    }
    else if (block >= (void*)((uint8_t*)mem->buffer + (mem->bsize * mem->bmax))) {
        /* Memory block pointer is out of range. */
        err = NOS_E_INV_VAL;
    }
    else if ((nOS_MemSize)((uint8_t*)block - (uint8_t*)mem->buffer) % mem->bsize != 0) {
        /* Memory block pointer is not a multiple of block size. */
        err = NOS_E_INV_VAL;
    }
    else if (mem->bcount == mem->bmax) {
        /* All blocks are already free. */
        err = NOS_E_OVERFLOW;
    }
    else {
        /* Memory block is already free? */
        void *p = (void*)mem->blist;
        while ((p != NULL) && (p != block)) {
            p = *(void**)p;
        }
        err = p == block ? NOS_E_OVERFLOW : NOS_OK;
    }

    return err;
}
#endif  /* NOS_CONFIG_MEM_SANITY_CHECK_ENABLE */

nOS_Error nOS_MemCreate (nOS_Mem *mem, void *buffer, nOS_MemSize bsize, nOS_MemCounter bmax)
{
    nOS_Error       err;
    nOS_StatusReg   sr;
    nOS_MemCounter  i;
    void            **blist;

#if (NOS_CONFIG_SAFE > 0)
    if (mem == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (buffer == NULL) {
        err = NOS_E_NULL;
    }
    else if (bsize < sizeof(void**)) {
        err = NOS_E_INV_VAL;
    } else
 #if (NOS_MEM_ALIGNMENT > 1)
  #if (NOS_MEM_POINTER_WIDTH == 8)
    if ((uint64_t)buffer % NOS_MEM_ALIGNMENT != 0)
  #elif (NOS_MEM_POINTER_WIDTH == 4)
    if ((uint32_t)buffer % NOS_MEM_ALIGNMENT != 0)
  #elif (NOS_MEM_POINTER_WIDTH == 2)
    if ((uint16_t)buffer % NOS_MEM_ALIGNMENT != 0)
  #endif
    {
        err = NOS_E_INV_VAL;
    } else
 #endif
    if (bmax == 0) {
        err = NOS_E_INV_VAL;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (mem->e.type != NOS_EVENT_INVALID) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            nOS_CreateEvent((nOS_Event*)mem
#if (NOS_CONFIG_SAFE > 0)
                           ,NOS_EVENT_MEM
#endif
                           );
            /* Initialize the single-link list */
            blist = NULL;
#if (NOS_CONFIG_MEM_SANITY_CHECK_ENABLE > 0)
            mem->buffer = buffer;
#endif
            for (i = 0; i < bmax-1; i++) {
                *(void**)buffer = blist;
                blist = (void**)buffer;
                buffer = (void*)((uint8_t*)buffer + bsize);
            }
            *(void**)buffer = blist;
            mem->blist  = (void**)buffer;
#if (NOS_CONFIG_MEM_SANITY_CHECK_ENABLE > 0)
            mem->bsize  = bsize;
            mem->bcount = bmax;
            mem->bmax   = bmax;
#endif

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

#if (NOS_CONFIG_MEM_DELETE_ENABLE > 0)
nOS_Error nOS_MemDelete (nOS_Mem *mem)
{
    nOS_Error       err;
    nOS_StatusReg   sr;

#if (NOS_CONFIG_SAFE > 0)
    if (mem == NULL) {
        err = NOS_E_INV_OBJ;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (mem->e.type != NOS_EVENT_MEM) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
            mem->blist  = NULL;
#if (NOS_CONFIG_MEM_SANITY_CHECK_ENABLE > 0)
            mem->buffer = NULL;
            mem->bsize  = 0;
            mem->bcount = 0;
            mem->bmax   = 0;
#endif
            nOS_DeleteEvent((nOS_Event*)mem);

            err = NOS_OK;
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}
#endif  /* NOS_CONFIG_MEM_DELETE_ENABLE */

void *nOS_MemAlloc(nOS_Mem *mem, nOS_TickCounter timeout)
{
    nOS_StatusReg   sr;
    void            *block;

#if (NOS_CONFIG_SAFE > 0)
    if (mem == NULL) {
        block = NULL;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (mem->e.type != NOS_EVENT_MEM) {
            block = NULL;
        } else
#endif
        if (mem->blist != NULL) {
            block = (void*)mem->blist;
            mem->blist = *(void***)block;
#if (NOS_CONFIG_MEM_SANITY_CHECK_ENABLE > 0)
            mem->bcount--;
#endif
        }
        else if (timeout == NOS_NO_WAIT) {
            /* Caller can't wait? Try again. */
            block = NULL;
        }
        else {
            block = NULL;
            nOS_runningThread->ext = (void*)&block;
            nOS_WaitForEvent((nOS_Event*)mem,
                             NOS_THREAD_ALLOC_MEM
#if (NOS_CONFIG_WAITING_TIMEOUT_ENABLE > 0)
                            ,timeout
#elif (NOS_CONFIG_SLEEP_ENABLE > 0) || (NOS_CONFIG_SLEEP_UNTIL_ENABLE > 0)
                            ,NOS_WAIT_INFINITE
#endif
                            );
        }
        nOS_LeaveCritical(sr);
    }

    return block;
}

nOS_Error nOS_MemFree(nOS_Mem *mem, void *block)
{
    nOS_Error       err;
    nOS_StatusReg   sr;
    nOS_Thread      *thread;

#if (NOS_CONFIG_SAFE > 0)
    if (mem == NULL) {
        err = NOS_E_INV_OBJ;
    }
    else if (block == NULL) {
        err = NOS_E_INV_VAL;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (mem->e.type != NOS_EVENT_MEM) {
            err = NOS_E_INV_OBJ;
        } else
#endif
        {
#if (NOS_CONFIG_MEM_SANITY_CHECK_ENABLE > 0)
            err = _SanityCheck(mem, block);
            if (err == NOS_OK)
#else
            err = NOS_OK;
#endif
            {
                thread = nOS_SendEvent((nOS_Event*)mem, NOS_OK);
                if (thread != NULL) {
                    *(void**)thread->ext = block;
#if (NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE > 0)
                    /* Verify if a highest prio thread is ready to run */
                    nOS_Schedule();
#endif
                }
                else {
                    *(void**)block = mem->blist;
                    mem->blist = (void**)block;
#if (NOS_CONFIG_MEM_SANITY_CHECK_ENABLE > 0)
                    mem->bcount++;
#endif
                }
            }
        }
        nOS_LeaveCritical(sr);
    }

    return err;
}

bool nOS_MemIsAvailable (nOS_Mem *mem)
{
    nOS_StatusReg   sr;
    bool            avail;

#if (NOS_CONFIG_SAFE > 0)
    if (mem == NULL) {
        avail = false;
    } else
#endif
    {
        nOS_EnterCritical(sr);
#if (NOS_CONFIG_SAFE > 0)
        if (mem->e.type != NOS_EVENT_MEM) {
            avail = false;
        } else
#endif
        {
            avail = (mem->blist != NULL);
        }
        nOS_LeaveCritical(sr);
    }

    return avail;
}
#endif  /* NOS_CONFIG_MEM_ENABLE */

#ifdef __cplusplus
}
#endif
