# Notes for Final

## Important!!
How to utilize pwn tools to find all symbols or addresses in a elf binary:
```python
from pwn import *
e = ELF("./challenge_binary", checksec=False)
for name, addr in e.symbols.items():
    print(hex(addr), name)
```

1. look for a symbols like `get_flag`, `print_flag`, `win`, etc.
    - Also for global vars: secret, key, val, canary.
    - Note the exact name, such as: `0x401424 get_flag`

2. Decompiling
```
r2 -AA ./chall
aaa
afl               # list functions
s main
pdd               # decompile main
s sym.get_input   # or decompile other functions
pdd
s sym.get_flag
pdd
```

3. Pattern Recognition - example from mooneys-bookstore
Stage 1:
```C
read(0, &addr, 8);
uint64_t value = *(uint64_t *)addr;
printf("%lx\n", value);   // leak secret key
```

```C
read(0, &key_input, 8);
if (key_input == secret_key) {
    get_input()
}
```

Stage 2: Inspecting get_input
```C
fread(&val, 8, 1, urandom);
local_val = val;
printf("0x%lx\n", val);   // leaks this random value that is like a canary
gets(buf);                // overflow this.
if (local_val != val) exit(1);   // integrity check / fake canary
```

Somewhere, there is this symbol/function that prints the flag.
```C
void get_flag() {
    system("cat flag.txt");
    _exit(0);
}
```

So the flow is, leak secret -> pass the gate with it -> leak canary value -> overwrite return instruction pointer (RIP).



## Instructing my agent
1. use ELF binary with pwntools to list symbols
2. Use `r2 -AAqc "aaa; s sym.func; pdda"` to decompile specific functions to C-like code.

1. Decompile main and look for vuln, or secret leak, etc.
2. Decompile helper function (sym.func) to look for further vuln.
3. Do the exploit, by computing stack layout for stack overflow, etc.
4. Construct stage by stage exploit with pwntools, for example:
    - stage1: leak and reuse key to pass through gate
    - stage2: leak value, and use it to overwrite RIP to reach flag.

* remind the agent about little-endian?

