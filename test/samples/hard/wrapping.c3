
module main;
import io;

function void main()
{
   var uint16_t a;
   a = 0xfffe;
   io.print2("a=", a);
   a = a + cast<uint16_t>(3);
   io.print2("a=", a);
   a = a - cast<uint16_t>(3);
   io.print2("a=", a);

   var uint8_t b;
   b = 0xfe;
   io.print2("b=", b);
   b = b + cast<uint8_t>(3);
   io.print2("b=", b);
   b = b - cast<uint8_t>(3);
   io.print2("b=", b);

  // TODO:
   //var uint32_t c;
   //c = 0xfffffffe;
   //io.print2("c=", cast<int32_t>(c));
   //c = c + cast<uint32_t>(3);
   //io.print2("c=", cast<int32_t>(c));
   //c = c - cast<uint32_t>(3);
   //io.print2("c=", cast<int32_t>(c));
}
