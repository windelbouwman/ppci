module kernel32;
/*
  Convenient wrapper around some win32 functions.
*/

public function int GetStdHandle(int n);
public function int WriteFile(int n, byte* buffer, int count, int* written, int overlapped);
