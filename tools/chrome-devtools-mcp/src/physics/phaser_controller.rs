// phaser_controller.rs
// Arkhe(n) Phaser Controller Driver - Rust

pub struct PhaserController {
    base_addr: *mut u32,
}

impl PhaserController {
    pub fn new(addr: *mut u32) -> Self {
        Self { base_addr: addr }
    }

    /// Ativa/Desativa o feixe Phaser (4.20 THz)
    pub unsafe fn set_enable(&mut self, enable: bool) {
        let reg = self.base_addr.add(0x00); // Control Register
        let val = if enable { 0x1 } else { 0x0 };
        core::ptr::write_volatile(reg, val);
    }

    /// Ajusta a fase do sintetizador
    pub unsafe fn set_phase(&mut self, phase_rad: f32) {
        let reg = self.base_addr.add(0x01); // Phase Register
        let val = (phase_rad * 1048576.0) as u32; // Scaling to internal units
        core::ptr::write_volatile(reg, val);
    }

    /// Lê o status de sincronia da cavidade
    pub unsafe fn get_sync_status(&self) -> u32 {
        let reg = self.base_addr.add(0x02); // Status Register
        core::ptr::read_volatile(reg)
    }
}
