export interface Vec2 {
    x: number;
    y: number;
}
export function vec2(x: number, y: number): Vec2 {
    return {x, y};
}

export function clamp(val: number, min: number, max: number): number {
    return Math.max(min, Math.min(max, val));
}

export function distancePointToRay(point: {x: number, y: number, z: number}, ray: {origin: {x: number, y: number, z: number}, direction: {x: number, y: number, z: number}}): number {
    // Simple point to line distance formula: ||(P-A) x D|| / ||D||
    const p_min_a = {
        x: point.x - ray.origin.x,
        y: point.y - ray.origin.y,
        z: point.z - ray.origin.z
    };

    // cross product
    const cross = {
        x: p_min_a.y * ray.direction.z - p_min_a.z * ray.direction.y,
        y: p_min_a.z * ray.direction.x - p_min_a.x * ray.direction.z,
        z: p_min_a.x * ray.direction.y - p_min_a.y * ray.direction.x
    };

    const cross_len = Math.sqrt(cross.x*cross.x + cross.y*cross.y + cross.z*cross.z);
    const dir_len = Math.sqrt(ray.direction.x*ray.direction.x + ray.direction.y*ray.direction.y + ray.direction.z*ray.direction.z);

    return dir_len === 0 ? Infinity : cross_len / dir_len;
}
