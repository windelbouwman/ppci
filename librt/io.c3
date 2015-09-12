module io;
import bsp;

public function void println(string txt)
{
    print(txt);
    bsp.putc(10); // Newline!
}

public function void print(string txt)
{
    var int i;
    i = 0;

    while (i < txt->len)
    {
        bsp.putc(txt->txt[i]);
        i = i + 1;
    }
}

// Print a sub part of a string
public function void print_sub(string txt, int start, int end)
{
    var int i;
    i = 0;

    i = start;
    while (i < end)
    {
        bsp.putc(txt->txt[i]);
        i = i + 1;
    }
}

// Print integer in hexadecimal notation:
public function void print_int(int i)
{
    print("0x");

    // int txt[20];
    var int b;
    var int c;
    c = 0;
    b = 0;

    for (b = 28; b >= 0; b = b - 4)
    {
        c = (i >> b) & 0xF;
        if (c < 10)
        {
            bsp.putc( 48 + c );
        }
        else
        {
            bsp.putc( 65 - 10 + c );
        }
    }

    bsp.putc(10); // Newline!
}

public function void print2(string label, int value)
{
    print(label);
    print_int(value);
}

