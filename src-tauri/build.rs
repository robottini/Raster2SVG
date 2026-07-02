fn main() {
    cc::Build::new()
        .include("vendor/potrace")
        .define("VERSION", "\"1.16\"")
        .warnings(false)
        .file("vendor/potrace/potracelib.c")
        .file("vendor/potrace/curve.c")
        .file("vendor/potrace/decompose.c")
        .file("vendor/potrace/trace.c")
        .compile("potrace");

    #[cfg(all(unix, not(target_os = "macos")))]
    println!("cargo:rustc-link-lib=m");

    tauri_build::build();
}
