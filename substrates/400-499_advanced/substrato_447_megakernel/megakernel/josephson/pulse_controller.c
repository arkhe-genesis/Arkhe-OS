#include "pulse_controller.h"
#include "josephson_driver.h"

int josephson_pid_control(int ring_id, double target_phi) {
    /* dummy implementation */
    if (rings[ring_id].phi < target_phi) rings[ring_id].phi += 0.002;
    else if (rings[ring_id].phi > target_phi) rings[ring_id].phi -= 0.002;
    return 0;
}
