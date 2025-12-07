hello_overflow

Goal:
  Trigger the win() function to print the flag.

Details:
  The program reads up to 64 bytes into a 32-byte buffer.
  Overflowing the buffer lets you overwrite the saved RIP and redirect execution.

Binary properties:
  - 64-bit
  - Non-PIE
  - No stack canaries
  - NX enabled

Compile with:
  gcc hello_overflow.c -o hello_overflow -fno-stack-protector -no-pie -z execstack
