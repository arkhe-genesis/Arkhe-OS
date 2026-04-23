#include <stdio.h>
#include <assert.h>
#include <math.h>
#include <string.h>
#include "../src/catedral/wormhole_metric.h"

void test_wormhole_curvature() {
    printf("Testing wormhole_curvature_from_s...\n");

    // Classical limit S=2.0 -> K=0
    assert(fabs(wormhole_curvature_from_s(2.0) - 0.0) < 1e-6);

    // Tsirelson limit S=2.82842712474619 -> K=inf
    // Use a value extremely close to or equal to BELL_TSIRELSON_LIMIT
    assert(isinf(wormhole_curvature_from_s(BELL_TSIRELSON_LIMIT)));

    // Intermediate value
    // S = 2.5 -> S^2 = 6.25
    // K = (6.25 - 4) / (8 - 6.25) = 2.25 / 1.75 = 1.285714...
    assert(fabs(wormhole_curvature_from_s(2.5) - 1.2857142857) < 1e-6);

    printf("Testing wormhole_classify...\n");
    assert(strcmp(wormhole_classify(-1.0), "INVALIDO") == 0);
    assert(strcmp(wormhole_classify(2.0), "INSTAVEL") == 0);
    assert(strcmp(wormhole_classify(5.0), "OPERACIONAL") == 0);
    assert(strcmp(wormhole_classify(12.0), "OTIMO") == 0);

    printf("All wormhole metric tests passed!\n");
}

int main() {
    test_wormhole_curvature();
    return 0;
}
