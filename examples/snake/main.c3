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
        game.single_step();
        bsp.sleep(100);
    }
}

