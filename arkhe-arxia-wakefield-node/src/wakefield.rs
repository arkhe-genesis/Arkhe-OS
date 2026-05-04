use core::fmt::Debug;

#[repr(C, packed)]
#[derive(Clone, Copy)]
pub struct WakefieldSnapshot {
    pub phase_error_scaled: i16,   // ×1000
    pub kt_gap_scaled: u16,        // ×500
    pub hallucination_flag: u8,
    pub timestamp: u32,            // segundos
    pub plasma_density: u16,       // ×1e15 cm⁻³
    pub alpha_scaled: i16,         // ×100000
    _reserved: [u8; 14],
}

impl WakefieldSnapshot {
    pub fn as_bytes(&self) -> [u8; 24] {
        unsafe { core::mem::transmute(*self) }
    }

    pub fn from_bytes(bytes: &[u8]) -> Option<Self> {
        if bytes.len() < core::mem::size_of::<Self>() { return None; }
        Some(unsafe { core::ptr::read_unaligned(bytes.as_ptr() as *const Self) })
    }
}

pub struct EmbeddedWakefieldAgent {
    pub phase_error: f32,
    pub kt_gap: f32,
    pub hallucination: bool,
    pub plasma_density: u16,
    pub alpha: f32,
}

impl EmbeddedWakefieldAgent {
    pub fn new() -> Self {
        Self {
            phase_error: 0.05,
            kt_gap: 1.0,
            hallucination: false,
            plasma_density: 100, // 1e17 cm⁻³
            alpha: 0.001,
        }
    }

    pub fn update_wakefield(&mut self, query_len: usize, context_len: usize) {
        self.kt_gap = (query_len as f32 / (context_len as f32 + 1.0) * 10.0).min(50.0);
        self.hallucination = self.kt_gap > 15.0;
        self.phase_error = (self.phase_error * 0.9 + self.kt_gap * 0.001).min(1.0);
        if self.hallucination {
            self.alpha *= 0.99;
        } else {
            self.alpha = (self.alpha + 0.00001).min(0.01);
        }
    }

    pub fn snapshot(&self) -> WakefieldSnapshot {
        WakefieldSnapshot {
            phase_error_scaled: (self.phase_error * 1000.0) as i16,
            kt_gap_scaled: (self.kt_gap * 500.0) as u16,
            hallucination_flag: if self.hallucination { 1 } else { 0 },
            timestamp: embassy_time::Instant::now().as_secs() as u32,
            plasma_density: self.plasma_density,
            alpha_scaled: (self.alpha * 100000.0) as i16,
            _reserved: [0u8; 14],
        }
    }
}
