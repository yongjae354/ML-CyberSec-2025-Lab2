#include <stdio.h>
#include <stdint.h>
#include <unistd.h>

uint64_t secret = 0x4142434445464748ULL;

void win() {
    printf("flag{pointer_practice_success}\n");
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);

    uint64_t addr;
    printf("Enter address: ");
    if (read(0, &addr, 8) != 8) return 1;

    uint64_t value = *(uint64_t *)addr;
    printf("%016lx\n", value);

    printf("Enter secret value: ");
    uint64_t guess;
    if (read(0, &guess, 8) != 8) return 1;

    if (guess == secret) win();
    else printf("Nope.\n");

    return 0;
}
