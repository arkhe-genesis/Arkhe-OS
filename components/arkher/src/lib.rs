use std::ffi::CString;

extern "C" {
    fn kolmogorov_gap(query: *const libc::c_char, source: *const libc::c_char, response: *const libc::c_char) -> f64;
    fn gap_to_finality(gap: f64) -> u32;
}

pub fn compute_gap(query: &str, source: &str, response: &str) -> f64 {
    let c_query = CString::new(query).unwrap();
    let c_source = CString::new(source).unwrap();
    let c_response = CString::new(response).unwrap();
    unsafe { kolmogorov_gap(c_query.as_ptr(), c_source.as_ptr(), c_response.as_ptr()) }
}

#[repr(u32)]
pub enum Finality {
    Pending = 0,
    L0 = 1,
    L1 = 2,
    L2 = 3,
}

pub fn gap_finality(gap: f64) -> Finality {
    match unsafe { gap_to_finality(gap) } {
        0 => Finality::Pending,
        1 => Finality::L0,
        2 => Finality::L1,
        3 => Finality::L2,
        _ => unreachable!(),
    }
}
