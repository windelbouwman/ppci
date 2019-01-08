/*
 LibreRTOS - Portable single-stack Real Time Operating System.

 Character FIFO. Specialized character queue. Read/write several characters with
 one read/write call.

 Copyright 2016 Djones A. Boni

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
 */
void enable_interrupts();
void entercritical();

#include "nOS.h"
#include "clib.h"
#include "timer.h"
#include "interrupt.h"
#include "murax.h"


#define FOO_STACK_SIZE             3*32*4
#define FOO_THREAD_PRIO            1

nOS_Thread FooHandle3;
nOS_Thread FooHandle9;
nOS_Stack  FooStack3[FOO_STACK_SIZE];
nOS_Stack  FooStack9[FOO_STACK_SIZE];

void Isr(void)
{
    TIMER_INTERRUPT->PENDINGS = 1; 
    nOS_Tick(1);
    //printf("Tick..\n");
} 

void Foo9(void *arg)
{
    NOS_UNUSED(arg);

    while (1) {
        //...

        nOS_SleepMs(9);
        printf("9ms Tick..\n");
    }
}

void Foo3(void *arg)
{
    NOS_UNUSED(arg);

    while (1) {
        //...

        nOS_SleepMs(3);
        printf("3ms Tick..\n");
    }
}
void main(void)
{
    //disable_interrupts();
    nOS_Error err;
    char *name1 = "Foo9";
    char *name2 = "Foo3";
    nOS_Init();
    // Application specific init
    nOS_InitSpecific();    
    
    interruptCtrl_init(TIMER_INTERRUPT);
	timer_init(TIMER_A);

	TIMER_PRESCALER->LIMIT = 500-1; //10us rate
	TIMER_A->LIMIT = 100-1;  //1 second rate
	TIMER_A->CLEARS_TICKS = 0x00010002;

	TIMER_INTERRUPT->PENDINGS = 0xF;
	TIMER_INTERRUPT->MASKS = 0x1; 
    
    // nOS objects creation
    err = nOS_ThreadCreate(&FooHandle9, Foo9, 0, &FooStack9[0], FOO_STACK_SIZE, 1, NOS_THREAD_READY, name1);
    err = nOS_ThreadCreate(&FooHandle3, Foo3, 0, &FooStack3[0], FOO_STACK_SIZE, 1, NOS_THREAD_READY, name2);
    if(err) printf("Err:%d\n",err);
    nOS_Start();   
    enable_interrupts();

    // ...

    while (1) {
        // Idle

        // ...
    }
}
 
 
