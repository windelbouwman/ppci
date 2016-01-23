/*

*/

module main;

import bsp;
import io;
import game;


public function void main()
{
    io.println("Welcome to snake!");

    game.init();
    game.single_step();

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

