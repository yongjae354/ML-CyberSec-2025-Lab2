echo_fmt

Goal:
  Leak the global secret using the format string vulnerability.
  Then enter the secret hex value to unlock the flag.

Hints:
  - printf(buf) is vulnerable.
  - Try %p, %lx, %7$p, etc.

Binary properties:
  - 64-bit
  - Non-PIE
  - Stack canary enabled
  - NX enabled

Compile with:
  gcc echo_fmt.c -o echo_fmt -Wl,-z,relro,-z,now -fstack-protector-all -no-pie
