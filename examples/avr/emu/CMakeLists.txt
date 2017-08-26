
cmake_minimum_required(VERSION 2.6)
project(emu1)

add_executable(emu1 main.c)
target_link_libraries(emu1 simavr)

add_executable(emu1_debug main.c)
target_link_libraries(emu1_debug simavr)
target_compile_definitions(emu1_debug PRIVATE WITH_GDB_DEBUG_SERVER)
