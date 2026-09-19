#![no_std]

use core::panic::PanicInfo;

mod memory;
mod scheduler;
mod syscalls;
mod ipc;
mod isolation;
mod temporal;
mod axiarchy;

#[no_mangle]
pub extern "C" fn kmain() -> ! {
    loop {}
}

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}
