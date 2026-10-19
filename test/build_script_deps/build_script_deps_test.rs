#[test]
fn injected_dependency_is_available_to_build_script() {
    assert_eq!(configured_build_script::message(), "injected build dependency");
}
