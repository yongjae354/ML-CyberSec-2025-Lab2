# Notes for Final

## Important!!
How to utilize pwn tools to find all symbols or addresses in a elf binary:

```python
from pwn import *
def find_symbols(path):
	try:
		elf = ELF(path)
		for name, address in elf.symbols.items():
			print(f"{hex(address)}: {name}")
	except Exception as e:
		raise e
```
