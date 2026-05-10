#include <stdio.h>
#include <stdint.h>

// Basic quaternion representation
typedef struct {
    int32_t w;
    int32_t x;
    int32_t y;
    int32_t z;
} Quaternion;

// Quaternion multiplication
Quaternion quat_mul(Quaternion q1, Quaternion q2) {
    Quaternion result;
    result.w = q1.w * q2.w - q1.x * q2.x - q1.y * q2.y - q1.z * q2.z;
    result.x = q1.w * q2.x + q1.x * q2.w + q1.y * q2.z - q1.z * q2.y;
    result.y = q1.w * q2.y - q1.x * q2.z + q1.y * q2.w + q1.z * q2.x;
    result.z = q1.w * q2.z + q1.x * q2.y - q1.y * q2.x + q1.z * q2.w;
    return result;
}

// Compare two quaternions
int quat_eq(Quaternion q1, Quaternion q2) {
    return q1.w == q2.w && q1.x == q2.x && q1.y == q2.y && q1.z == q2.z;
}

int main() {
    // A simple OVT test: compare (A * B) * C with A * (B * C)
    // Non-associative logic is simulated here for the proof
    int w1, x1, y1, z1;
    int w2, x2, y2, z2;
    int w3, x3, y3, z3;

    // Read 3 quaternions
    scanf("%d %d %d %d", &w1, &x1, &y1, &z1);
    scanf("%d %d %d %d", &w2, &x2, &y2, &z2);
    scanf("%d %d %d %d", &w3, &x3, &y3, &z3);

    Quaternion q1 = {w1, x1, y1, z1};
    Quaternion q2 = {w2, x2, y2, z2};
    Quaternion q3 = {w3, x3, y3, z3};

    Quaternion q12 = quat_mul(q1, q2);
    Quaternion lhs = quat_mul(q12, q3); // (A * B) * C

    Quaternion q23 = quat_mul(q2, q3);
    Quaternion rhs = quat_mul(q1, q23); // A * (B * C)

    if (quat_eq(lhs, rhs)) {
        // If associative
        asm("CALL Proof");
    } else {
        // If non-associative
        asm("CALL Cheat");
    }

    return 0;
}
