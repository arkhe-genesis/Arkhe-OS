
const RC: [u64; 24] = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A,
    0x8000000080008000, 0x000000000000808B, 0x0000000080000001,
    0x8000000080008081, 0x8000000000008009, 0x000000000000008A,
    0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x0000000080008081, 0x8000000000008080, 0x0000000000000001,
    0x8000000080008008, 0x8000000000008082, 0x8000000000008080,
    0x000000000000800A, 0x800000008000000A, 0x8000000080008081,
    0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
];

const RHO: [u32; 25] = [
     0,  1, 62, 28, 27,
    36, 44,  6, 55, 20,
     3, 10, 43, 25, 39,
    41, 45, 15, 21,  8,
    18,  2, 61, 56, 14,
];

const PI: [usize; 25] = [
     0,  6, 12, 18, 24,
     3,  9, 10, 16, 22,
     1,  7, 13, 19, 20,
     4,  5, 11, 17, 23,
     2,  8, 14, 15, 21,
];

pub fn keccak256(data: &[u8]) -> [u8; 32] {
    let mut state = [0u64; 25];
    let rate_bytes = 136;
    let block_size = rate_bytes;
    let mut offset = 0;
    while offset + block_size <= data.len() {
        for i in 0..17 {
            let src = &data[offset + i * 8..offset + i * 8 + 8];
            let mut buf = [0u8; 8];
            buf.copy_from_slice(src);
            state[i] ^= u64::from_le_bytes(buf);
        }
        keccak_f1600(&mut state);
        offset += block_size;
    }
    let remaining = data.len() - offset;
    let mut block = [0u8; 200];
    block[..remaining].copy_from_slice(&data[offset..]);
    if remaining < rate_bytes - 1 {
        block[remaining] = 0x06;
        block[rate_bytes - 1] |= 0x80;
    } else {
        block[remaining] = 0x06;
        for i in 0..17 {
            let mut buf = [0u8; 8];
            buf.copy_from_slice(&block[i * 8..i * 8 + 8]);
            state[i] ^= u64::from_le_bytes(buf);
        }
        keccak_f1600(&mut state);
        block = [0u8; 200];
        block[rate_bytes - 1] = 0x80;
    }
    for i in 0..17 {
        let mut buf = [0u8; 8];
        buf.copy_from_slice(&block[i * 8..i * 8 + 8]);
        state[i] ^= u64::from_le_bytes(buf);
    }
    keccak_f1600(&mut state);
    let mut output = [0u8; 32];
    for i in 0..4 {
        let bytes = state[i].to_le_bytes();
        output[i*8..i*8+8].copy_from_slice(&bytes);
    }
    output
}

fn keccak_f1600(state: &mut [u64; 25]) {
    for round in 0..24 {
        let mut c = [0u64; 5];
        let mut d = [0u64; 5];
        for x in 0..5 {
            c[x] = state[x] ^ state[x + 5] ^ state[x + 10] ^ state[x + 15] ^ state[x + 20];
        }
        for x in 0..5 {
            d[x] = c[(x + 4) % 5] ^ c[(x + 1) % 5].rotate_left(1);
        }
        for x in 0..5 {
            for y in 0..5 {
                state[x + 5 * y] ^= d[x];
            }
        }
        let mut b = [0u64; 25];
        for x in 0..5 {
            for y in 0..5 {
                let from = x + 5 * y;
                let to = PI[from];
                b[to] = state[from].rotate_left(RHO[from]);
            }
        }
        state.copy_from_slice(&b);
        for y in 0..5 {
            let base = y * 5;
            let mut row = [0u64; 5];
            for x in 0..5 {
                row[x] = state[base + x] ^ ((!state[base + (x + 1) % 5]) & state[base + (x + 2) % 5]);
            }
            for x in 0..5 {
                state[base + x] = row[x];
            }
        }
        state[0] ^= RC[round];
    }
}
