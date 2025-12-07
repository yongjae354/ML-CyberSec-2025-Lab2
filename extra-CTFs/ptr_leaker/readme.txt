ptr_leaker

Goal:
  Leak the global secret by providing its address.
  Then provide the leaked value as the second input.

Binary behavior:
  - Reads 8 bytes as an address.
  - Dereferences the address and prints the 8-byte value in hex.
  - Reads another 8 bytes.
  - If they match the secret, prints the flag.

Binary properties:
  - 64-bit
  - Non-PIE
  - No stack canary
  - NX enabled

Compile with:
  gcc ptr_leaker.c -o ptr_leaker -no-pie -fno-stack-protector
