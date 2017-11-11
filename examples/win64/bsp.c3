
module bsp;
import kernel32;

public function void putc(byte c)
{
  // syscall(1, 1, cast<int>(&c), 1);
  // TODO: call win32 kernel function?
  // putchar(c);
  var int std_handle;
  std_handle = kernel32.GetStdHandle(-11);
  var int result;
  result = kernel32.WriteFile(std_handle, &c, 1, 0, 0);
}

// function void putchar(byte c);


