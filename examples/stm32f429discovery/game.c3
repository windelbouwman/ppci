
module game;

const int max_body_len = 10;

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

type int[10][10] map_t;

var body_t body;
var map_t map;

function void increment_ptr(int* ptr)
{
    (*ptr) += 1;
    if (*ptr >= max_body_len)
    {
        *ptr = 0;
    }
}

function void step()
{
    var int x, y, dx, dy;

    x = body.elements[body.head].x;
    y = body.elements[body.head].y;

    if (body.direction == 0)
    {
        dx = 0;
        dy = -1;
    }

    if (body.direction == 1)
    {
        dx = -1;
        dy = 0;
    }

    if (body.direction == 2)
    {
        dx = 0;
        dy = 1;
    }

    if (body.direction == 3)
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

