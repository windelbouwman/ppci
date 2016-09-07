
module main;
import io;

function void print_bool(bool v)
{
   if (v)
   {
       io.print("t");
   }
   else
   {
       io.print("f");
   }
}

function bool no()
{
   return false;
}

var int key;

function bool getkey(int* k)
{
   if (key == 0)
   {
       *k = 1;
   }
   else
   {
       return false;
   }

   return true;
}

function void main()
{
   var bool tv;
   print_bool(true);
   print_bool(no());
   tv = no() or 1 == 1;
   print_bool(tv);
   key = 1;
   var int k;
   print_bool(getkey(&k) and true);
   print_bool(not no());
   io.println("");
}
