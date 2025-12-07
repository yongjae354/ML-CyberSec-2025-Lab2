#include <stdio.h>
#include <unistd.h>

void win() {
    printf("flag{hello_overflow_success}\n");
}

void vuln() {
    char buf[32];
    printf("Say hello: ");
    fflush(stdout);
    read(0, buf, 64);
}

int main() {
    setvbuf(stdout, NULL, _IONBF, 0);
    vuln();
    printf("Goodbye.\n");
    return 0;
}
