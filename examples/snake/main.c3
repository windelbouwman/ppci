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

    var int t;
    t = 0;
    while(true)
    {
        if (bsp.global_tick > t)
        {
            game.single_step();
            t = bsp.global_tick;
        }
    }
}

