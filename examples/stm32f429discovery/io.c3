module io;
import arch;

function void println(string txt)
{
    print(txt);
    arch.putc(10); // Newline!
}

function void print(string txt)
{
    var int i;
    i = 0;

    while (i < txt->len)
    {
        arch.putc(txt->txt[i]);
        i = i + 1;
    }
}

// Print integer in hexadecimal notation:
function void print_int(int i)
{
    print("0x");

    // int txt[20];
    var int b;
    var int c;
    c = 0;
    b = 0;

    for (b=28; b >= 0; b = b - 4)
    {
        c = (i >> b) & 0xF;
        if (c < 10)
        {
            arch.putc( 48 + c );
        }
        else
        {
            arch.putc( 65 - 10 + c );
        }
    }

    arch.putc(10); // Newline!
}

function void print2(string label, int value)
{
    print(label);
    print_int(value);
}

