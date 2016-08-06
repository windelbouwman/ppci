
cmake_minimum_required(VERSION 2.6)
project(emu1)
add_executable(emu1 main.c)
target_link_libraries(emu1 simavr)
