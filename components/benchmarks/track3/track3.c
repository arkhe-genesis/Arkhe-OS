#include <stdio.h>

int main() {
    int iterations;
    scanf("%d", &iterations);

    // Very simple arithmetic block
    int sum = 0;
    for (int i = 0; i < 50; i++) {
        sum += i * 3 - 2;
    }

    if (sum >= 0) {
        asm("CALL Proof");
    } else {
        asm("CALL Cheat");
    }

    return 0;
}
