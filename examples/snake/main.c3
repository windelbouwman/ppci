/*

*/

module main;

import bsp;
import io;
import game;


function void main()
{
    io.println("Welcome to snake!");

    game.init();

    while(true)
    {
        game.single_step();
    }
}

