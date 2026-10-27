#[test]
fn runtime_linking_needs_no_sdk_at_build_time() {
    let path = std::path::Path::new("/rules-rs-repro/no-aic-sdk");
    let error = unsafe { aic_sdk_sys::load_library(path) }.unwrap_err();
    match error {
        aic_sdk_sys::DynamicLoadingError::OpenLibrary {
            path: attempted, ..
        } => {
            assert_eq!(attempted, path);
        }
        error => panic!("unexpected loader error: {error}"),
    }
}
