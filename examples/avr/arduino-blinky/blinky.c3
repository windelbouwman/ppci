module main;

function void on();
function void off();
function void delay(int x);

function void main()
{
   while(true)
   {
    on();
    delay(10);
    off();
    delay(40);
   }
}

