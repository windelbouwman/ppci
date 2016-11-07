
module main;
import io;

const float pi = 3.14159;

function float area(float radius)
{
  return radius * radius * pi;
}

function float wfun(float a, float b)
{
  return (a * 66) + (b * 33 + 11);
}

function void main()
{
  var float[8] buffer;
  buffer[0] = 0;
  buffer[1] = 22;
  buffer[2] = 3.1415926;
  buffer[3] = 2.7;
  buffer[4] = wfun(buffer[1], buffer[2]);

  if (buffer[1] > buffer[0])
  {
    io.print("for sure");
  }

  if (buffer[1] > wfun(buffer[2], buffer[3]))
  {
    io.print("woot more");
  }

  if (area(buffer[1]) < buffer[2])
  {
    io.print("woot less");
  }

  io.print2("area(22)=", cast<int>(area(22)));
}

