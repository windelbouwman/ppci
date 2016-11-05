
module main;
import io;

const float pi = 3.14159;

function float circumference(float radius)
{
  return pi * 2 * radius;
}

function float area(float radius)
{
  return radius * radius * pi;
}

function void main()
{
    io.print2("area(2)=", cast<int>(area(2)));
    io.print2("circumference(2)=", cast<int>(circumference(2)));
    io.print2("area(3)=", cast<int>(area(3)));
    io.print2("circumference(3)=", cast<int>(circumference(3)));
}

