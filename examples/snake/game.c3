
module game;
import bsp;

const int max_body_len = 10;
const int grid_size = 10;
const int UP = 0, LEFT = 1, DOWN = 2, RIGHT = 3;

type struct {
    struct
    {
        int x;
        int y;
    }[max_body_len] elements;
    int head;
    int tail;
    int direction;
} body_t;

type int[grid_size][grid_size] map_t;

// Global variables with state info:
var body_t body;
var map_t map;
var map_t render;

function void init()
{
    var int i;
    for (i = 0; i < grid_size; i += 1)
    {
        map[i][0] = 1;
        map[i][9] = 1;
        map[0][i] = 1;
        map[9][i] = 1;
    }
}

function void increment_ptr(int* ptr)
{
    (*ptr) += 1;
    if (*ptr >= max_body_len)
    {
        *ptr = 0;
    }
}

// Advance the snake one step
function void step_snake()
{
    var int x, y, dx, dy;

    x = body.elements[body.head].x;
    y = body.elements[body.head].y;

    if (body.direction == UP)
    {
        dx = 0;
        dy = -1;
    }

    if (body.direction == LEFT)
    {
        dx = -1;
        dy = 0;
    }

    if (body.direction == DOWN)
    {
        dx = 0;
        dy = 1;
    }

    if (body.direction == RIGHT)
    {
        dx = 1;
        dy = 0;
    }

    x += dx;
    y += dy;

    increment_ptr(&body.head);
    increment_ptr(&body.tail);

    body.elements[body.head].x = x;
    body.elements[body.head].y = y;
}

// Copy map and snake to display
function void make_output()
{
    var int x, y;

    // Blit map to render:
    for (x = 0; x < grid_size; x += 1)
    {
        for (y = 0; y < grid_size; y += 1)
        {
            if (map[x][y] == 0)
            {
                render[x][y] = 32;
            }
            else
            {
                render[x][y] = 65;
            }
        }
    }

    // TODO:
    // Render snake to render:
    //
}

function void print_render()
{
    var int x, y;

    // Blit map to render:
    for (y = 0; y < grid_size; y += 1)
    {
        for (x = 0; x < grid_size; x += 1)
        {
            bsp.putc(render[x][y]);
        }

        bsp.putc(10);
    }
}

// Perform all actions for a tick in the game
function void single_step()
{
    step_snake();
    make_output();
    print_render();
}

