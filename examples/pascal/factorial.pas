program exRecursion;
  var
  num, f: integer;
  function fact(x: integer): integer;
  begin
  if x=0 then
    fact := 1
  else
    fact := x * fact(x- 1);
  end;
begin
  writeln('enter number:');
  num := 4;
  {readln(num);}
  f := fact(num);
  writeln('Factorial', num, 'is:', f);
end.
