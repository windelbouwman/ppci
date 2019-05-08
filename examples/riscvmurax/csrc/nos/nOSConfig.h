#define NOS_PRIVATE                            
/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable debug code. Initialize thread's registers and stack to known values (useful to know how much     *
 * space of the stack is used by the thread).                                                                         *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can be disable when application will be debugged to decrease flash space used.                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_DEBUG                            1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable arguments checking in nOS API.                                                                   *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can be disable when application will be debugged to increase performance and decrease flash space used.       *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SAFE                             1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Highest priority a thread can have (0 to 255 inclusively). Set to 0 to enable a cooperative scheduling with all    *
 * threads at the same priority (preemptive scheduling need to be disabled).                                          *
 *                                                                                                                    *
 * 0   = Lowest priority                                                                                              *
 * 255 = Highest priority                                                                                             *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. It is recommenced to set the thread highest priority adjusted to the minimum required by the application to   *
 *      minimize memory used by the scheduler.                                                                        *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_HIGHEST_THREAD_PRIO              31

/**********************************************************************************************************************
 *                                                                                                                    *
 * Size of ticks counter for sleep/timeout in bits (can be 8, 16, 32 and 64).                                         *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Bits width directly affects the maximum timeout that the application can specify to nOS API.                  *
 *   2. For maximum performance, it is recommenced to set width of a CPU register.                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TICK_COUNT_WIDTH                 32

/**********************************************************************************************************************
 *                                                                                                                    *
 * Number of ticks per second. nOS_MsToTicks and nOS_SleepMs use this value to convert ms to ticks.                   *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. It is recommended to don't go higher than 1000 ticks per second.                                              *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TICKS_PER_SECOND                 1000

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable preemptive scheduler. When enabled, the scheduler will ensure it's always the highest priority   *
 * ready to run thread that is running. If disabled, threads use a cooperative scheduling.                            *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Need to be disabled if highest thread priority equal to 0.                                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SCHED_PREEMPTIVE_ENABLE          1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable round-robin scheduler. If enabled, each tick will try to switch thread context to another ready  *
 * to run thread of the same priority.                                                                                *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Not used if preemptive scheduling is disabled.                                                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SCHED_ROUND_ROBIN_ENABLE         1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable lock/unlock scheduler.                                                                           *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Not useful when application need a cooperative scheduling.                                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SCHED_LOCK_ENABLE                1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable sleeping from running thread.                                                                    *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can't sleep from main thread (idle).                                                                          *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SLEEP_ENABLE                     1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable sleeping from running thread until reaching specified tick counter. Used to create timed thread. *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can't sleep from main thread (idle).                                                                          *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SLEEP_UNTIL_ENABLE               1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable resuming and suspending thread at run-time.                                                      *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. If disabled, application can't specify state of the thread at creation.                                       *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_THREAD_SUSPEND_ENABLE            1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable resuming and suspending all threads at same time.                                                *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Not used if NOS_CONFIG_THREAD_SUSPEND_ENABLE is disabled.                                                     *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_THREAD_SUSPEND_ALL_ENABLE        1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable deleting thread at run-time.                                                                     *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_THREAD_DELETE_ENABLE             1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable aborting waiting operations.                                                                     *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_THREAD_ABORT_ENABLE              1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable changing priority of thread at run-time.                                                         *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_THREAD_SET_PRIO_ENABLE           1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable thread naming (useful for debugging).                                                            *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. If enabled, application need to give constant string pointer at thread creation.                              *
 *   2. Thread name can be changed at run-time.                                                                       *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_THREAD_NAME_ENABLE               1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable joining thread (waiting for other thread to complete).                                           *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_THREAD_JOIN_ENABLE               0

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable variable timeout when thread trying to take sem, lock mutex, wait on flags, ...                  *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. If disabled, everything other than NOS_NO_WAIT for timeout is equivalent to NOS_WAIT_INFINITE.                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_WAITING_TIMEOUT_ENABLE           1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable semaphore.                                                                                       *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can be disabled if not needed by the application to decrease flash space used.                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SEM_ENABLE                       1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable deleting semaphore at run-time.                                                                  *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SEM_DELETE_ENABLE                1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Semaphore count width in bits (can be 8, 16, 32 or 64).                                                            *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Bits width directly affects the maximum number of times that a semaphore can be took.                         *
 *   2. For maximum performance, it is recommenced to set width of a CPU register.                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SEM_COUNT_WIDTH                  32

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable mutex.                                                                                           *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can be disabled if not needed by the application to decrease flash space used.                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_MUTEX_ENABLE                     1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable deleting mutex at run-time.                                                                      *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_MUTEX_DELETE_ENABLE              1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Mutex count width in bits (can be 8, 16, 32 or 64).                                                                *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Bits width directly affects the maximum number of times that a mutex can be locked.                           *
 *   2. For maximum performance, it is recommenced to set width of a CPU register.                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_MUTEX_COUNT_WIDTH                32

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable flag.                                                                                            *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can be disabled if not needed by the application to decrease flash space used.                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_FLAG_ENABLE                      1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable deleting flag at run-time.                                                                       *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_FLAG_DELETE_ENABLE               1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Size of flag in number of bits (can be 8, 16, 32 or 64).                                                           *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Bits width directly affects the number of different bits that can be held by flag.                            *
 *   2. For maximum performance, it is recommenced to set width of a CPU register.                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_FLAG_NB_BITS                     32

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable queue.                                                                                           *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can be disabled if not needed by the application to decrease flash space used.                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_QUEUE_ENABLE                     1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable deleting queue at run-time.                                                                      *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_QUEUE_DELETE_ENABLE              1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Queue block count width in bits (can be 8, 16, 32 or 64).                                                          *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Bits width directly affects the maximum count of block that can be stored in queue.                           *
 *   2. For maximum performance, it is recommenced to set width of a CPU register.                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_QUEUE_BLOCK_COUNT_WIDTH          32

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable fixed-sized array of memory block.                                                               *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can be disabled if not needed by the application to decrease flash space used.                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_MEM_ENABLE                       1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable deleting of memory array at run-time.                                                            *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_MEM_DELETE_ENABLE                1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Memory block size width in bits (can be 8, 16, 32 or 64).                                                          *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Bits width directly affects the maximum size of block that can be allocated from memory.                      *
 *   2. For maximum performance, it is recommenced to set width of a CPU register.                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_MEM_BLOCK_SIZE_WIDTH             32

/**********************************************************************************************************************
 *                                                                                                                    *
 * Memory block count width in bits (can be 8, 16, 32 or 64).                                                         *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Bits width directly affects the maximum count of block that can be allocated from memory.                     *
 *   2. For maximum performance, it is recommenced to set width of a CPU register.                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_MEM_BLOCK_COUNT_WIDTH            32

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable sanity check of pointer when they are freed (useful for debugging).                              *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. If enabled, freeing memory block can return error if pointer has been corrupted.                              *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_MEM_SANITY_CHECK_ENABLE          1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable timer with callback.                                                                             *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can be disabled if not needed by the application to decrease flash space used.                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIMER_ENABLE                     1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable deleting timer at run-time.                                                                      *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIMER_DELETE_ENABLE              1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Highest priority a timer can take (0 to 7 inclusively). Set to 0 to disable timer priority with all timers at      *
 * the same priority.                                                                                                 *
 *                                                                                                                    *
 * 0 = Lowest priority                                                                                                *
 * 7 = Highest priority                                                                                               *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. It is recommenced to set the timer highest priority adjusted to the minimum required by the application to    *
 *      minimize memory consumed.                                                                                     *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIMER_HIGHEST_PRIO               0

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable timer tick from nOS_Tick.                                                                        *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. If disabled, application is responsible to call nOS_TimerTick.                                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIMER_TICK_ENABLE                1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable timer thread that will take care of callback.                                                    *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. If disabled, application is responsible to call nOS_TimerProcess.                                             *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIMER_THREAD_ENABLE              1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Priority of timer thread.                                                                                          *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Not used if timer thread is disabled.                                                                         *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIMER_THREAD_PRIO                1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Stack size of timer thread.                                                                                        *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Not used if timer thread is disabled.                                                                         *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIMER_THREAD_STACK_SIZE          3*32*4

/**********************************************************************************************************************
 *                                                                                                                    *
 * Call stack size of timer thread.                                                                                   *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Only available on AVR platform with IAR compiler.                                                             *
 *   2. Not used if timer thread is disabled.                                                                         *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIMER_THREAD_CALL_STACK_SIZE     16

/**********************************************************************************************************************
 *                                                                                                                    *
 * Timer counter width in bits (can be 8, 16, 32 or 64).                                                              *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Bits width directly affects the maximum number of ticks that a timer can count.                               *
 *   2. For maximum performance, it is recommenced to set width of a CPU register.                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIMER_COUNT_WIDTH                32

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable signal callback (can be used like software IRQ or any asynchronous event).                       *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can be disabled if not needed by the application to decrease flash space used.                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SIGNAL_ENABLE                    1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable deleting signal at run-time.                                                                     *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SIGNAL_DELETE_ENABLE             1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Highest priority a signal can take (0 to 7 inclusively). Set to 0 to disable signal priority with all signals at   *
 * the same priority.                                                                                                 *
 *                                                                                                                    *
 * 0 = Lowest priority                                                                                                *
 * 7 = Highest priority                                                                                               *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. It is recommenced to set the signal highest priority adjusted to the minimum required by the application to   *
 *      minimize memory consumed.                                                                                     *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SIGNAL_HIGHEST_PRIO              0

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable signal thread that will take care of callback.                                                   *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. If disabled, application is responsible to call nOS_SignalProcess.                                            *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SIGNAL_THREAD_ENABLE             1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Priority of signal thread.                                                                                         *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Not used if signal thread is disabled.                                                                        *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SIGNAL_THREAD_PRIO               1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Stack size of signal thread.                                                                                       *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Not used if signal thread is disabled.                                                                        *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SIGNAL_THREAD_STACK_SIZE         3*32*4

/**********************************************************************************************************************
 *                                                                                                                    *
 * Call stack size of signal thread.                                                                                  *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Only available on AVR platform with IAR compiler.                                                             *
 *   2. Not used if signal thread is disabled.                                                                        *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_SIGNAL_THREAD_CALL_STACK_SIZE    16

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable time management.                                                                                 *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can be disabled if not needed by the application to decrease flash space used.                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIME_ENABLE                      1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable time tick from nOS_Tick.                                                                         *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. If disabled, application is responsible to call nOS_TimeTick.                                                 *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIME_TICK_ENABLE                 1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable waiting for specific time and date from running thread.                                          *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can't sleep from main thread (idle).                                                                          *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIME_WAIT_ENABLE                 1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Number of time ticks per second. Time need this value to know how much ticks equal to 1 second.                    *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. It is recommended to don't go higher than 1000 ticks per second.                                              *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIME_TICKS_PER_SECOND            NOS_CONFIG_TICKS_PER_SECOND

/**********************************************************************************************************************
 *                                                                                                                    *
 * Time ticks counter width in bits (can be 32 or 64).                                                                *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Bits width directly affects the highest time/date that can be represented.                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_TIME_COUNT_WIDTH                 32

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable alarm management.                                                                                *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can be disabled if not needed by the application to decrease flash space used.                                *
 *   2. Alarm management is dependant from Time module.                                                               *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_ALARM_ENABLE                     1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable deleting alarm at run-time.                                                                      *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_ALARM_DELETE_ENABLE              1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable alarm tick from nOS_Tick.                                                                        *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. If disabled, application is responsible to call nOS_AlarmTick.                                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_ALARM_TICK_ENABLE                1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable alarm thread that will take care of callback.                                                    *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. If disabled, application is responsible to call nOS_AlarmProcess.                                             *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_ALARM_THREAD_ENABLE              1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Priority of alarm thread.                                                                                          *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Not used if alarm thread is disabled.                                                                         *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_ALARM_THREAD_PRIO                1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Stack size of alarm thread.                                                                                        *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Not used if alarm thread is disabled.                                                                         *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_ALARM_THREAD_STACK_SIZE          3*32*4

/**********************************************************************************************************************
 *                                                                                                                    *
 * Call stack size of alarm thread.                                                                                   *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Only available on AVR platform with IAR compiler.                                                             *
 *   2. Not used if alarm thread is disabled.                                                                         *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_ALARM_THREAD_CALL_STACK_SIZE     16

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable barrier.                                                                                         *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Can be disabled if not needed by the application to decrease flash space used.                                *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_BARRIER_ENABLE                   1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Enable or disable deleting barrier at run-time.                                                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_BARRIER_DELETE_ENABLE            1

/**********************************************************************************************************************
 *                                                                                                                    *
 * Stack size to use from interrupt service routines in number of nOS_Stack entries.                                  *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Not used on all platforms.                                                                                    *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_ISR_STACK_SIZE                   3*32*4

/**********************************************************************************************************************
 *                                                                                                                    *
 * Add possibility to override NVIC_PRIO_BITS if CMSIS is not used.                                                   *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Only available on ARM_Cortex_Mx plaforms, not used on the others.                                             *
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_NVIC_PRIO_BITS                   4

/**********************************************************************************************************************
 *                                                                                                                    *
 * Highest priority of interrupt service routines that use nOS API. It can enable zero interrupt latency for high     *
 * priority ISR. Application should not call any nOS API from interrupt service routines with priority higher than    *
 * this setting.                                                                                                      *
 *                                                                                                                    *
 * Lower number  = Higher priority (except PIC24)                                                                     *
 * Higher number = Lower priority (except PIC24)                                                                      *
 *                                                                                                                    *
 * Notes                                                                                                              *
 *   1. Not used on all platforms.                                                                                    *
 *   2. Can be set to zero to disable zero interrupt latency feature and completely disable interrupts in critical    *
 *      section (only applicable to ARM Cortex M3, M4 and M7).
 *                                                                                                                    *
 **********************************************************************************************************************/
#define NOS_CONFIG_MAX_UNSAFE_ISR_PRIO              5
