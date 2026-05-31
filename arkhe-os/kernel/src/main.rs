#![no_std]
#![no_main]

use core::panic::PanicInfo;

mod memory;
mod scheduler;
mod syscalls;
mod ipc;
mod isolation;
mod temporal;

#[no_mangle]
pub extern "C" fn _start() -> ! {
    loop {}
}

#[panic_handler]
fn panic(_info: &PanicInfo) -> ! {
    loop {}
}
