#include <stdio.h>
#include <stdlib.h>

unsigned long secret = 0x1337133713371337;

void win() {
    printf("flag{fmt_string_master}\n");
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);

    char buf[128];
    printf("Say something: ");
    fgets(buf, sizeof(buf), stdin);

    printf(buf); // format string vulnerability

    printf("\nEnter the secret (hex): ");
    unsigned long guess;
    scanf("%lx", &guess);

    if (guess == secret) {
        win();
    } else {
        printf("Nope.\n");
    }
}
