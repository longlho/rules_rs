pub fn sdk_version() -> unsafe fn() -> *const std::ffi::c_char {
    aic_sdk_sys::aic_get_sdk_version
}
