// kernel/src/syscalls.rs

use crate::temporal;
use crate::scheduler;
use crate::axiarchy;

#[repr(usize)]
pub enum Syscall {
    AnchorProof = 0x923,
    VerifyHumanity = 0x989,
    Infer100T = 0x9893,
    BinduMemory = 0x952,
    MeshRoute = 0x972,
    KyberEncrypt = 0x955,
    IpfsPin = 0x9721,
    NostrPublish = 0x973,
    TorRoute = 0x974,
    KernelIsolate = 0x9892,
    Evolve = 0x986,
    SelfHeal = 0x985,
    FairMetrics = 0x9895,
    ThesisGet = 0x965,
    AxiarchyVerify = 0x954,
}

#[no_mangle]
pub extern "C" fn syscall_handler(
    syscall_num: usize,
    arg1: usize,
    arg2: usize,
    arg3: usize,
) -> usize {
    if syscall_num == Syscall::AnchorProof as usize {
        temporal::anchor(arg1, arg2, arg3)
    } else if syscall_num == Syscall::ThesisGet as usize {
        scheduler::get_theosis(arg1 as u32)
    } else if syscall_num == Syscall::AxiarchyVerify as usize {
        axiarchy::verify_code(arg1)
    } else {
        0
    }
}
