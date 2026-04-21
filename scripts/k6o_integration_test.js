import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    vus: 10,
    duration: '30s',
};

export default function () {
    const url = 'http://localhost:8080/api/v1/gameplay/event';
    const payload = JSON.stringify({
        game_id: 'gta-vi-palmetto',
        player_id: 'tester',
        action: 'drive_vehicle',
        target: { entity_type: 'vehicle_van', entity_id: 'van-123' },
        position: { x: 10, y: 0, z: 20 }
    });

    const params = {
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer k6o_test_token',
        },
    };

    const res = http.post(url, payload, params);
    check(res, {
        'status is 202': (r) => r.status === 202,
    });
    sleep(1);
}
