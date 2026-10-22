fn main() {
    println!("cargo:rustc-env=BUILD_SCRIPT_MESSAGE={}", build_helper::message());
}
