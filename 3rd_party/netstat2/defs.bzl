"""netstat2's Apple bindings, without a host SDK or a Cargo build script."""

load("@bazel_lib//lib:copy_to_directory.bzl", "copy_to_directory")
load("@rules_cc//cc:defs.bzl", "cc_library")
load("@rules_rs//rs:rules_rust_bindgen.bzl", "rust_bindgen")
load("@rules_rust//rust:rust_common.bzl", "BuildInfo")

def _build_info_impl(ctx):
    return [BuildInfo(
        compile_data = depset(),
        dep_env = None,
        flags = None,
        linker_flags = None,
        link_search_paths = None,
        out_dir = ctx.file.out_dir,
        rustc_env = None,
    )]

_build_info = rule(
    implementation = _build_info_impl,
    attrs = {"out_dir": attr.label(allow_single_file = True, mandatory = True)},
)

def netstat2_bindings(name):
    """Supplies libproc_bindings.rs in OUT_DIR for macOS and iOS consumers.

    Args:
        name: Name of the BuildInfo target.
    """
    cc_library(
        name = name + "_header",
        hdrs = [Label("//3rd_party/netstat2:libproc_wrapper.h")],
    )
    rust_bindgen(
        name = "libproc_bindings",
        header = Label("//3rd_party/netstat2:libproc_wrapper.h"),
        cc_lib = ":" + name + "_header",
        bindgen_flags = ["--no-layout-tests"],
        clang_flags = ["-x", "c++"],
    )
    copy_to_directory(
        name = name + "_out_dir",
        srcs = [":libproc_bindings"],
    )
    _build_info(
        name = name,
        out_dir = ":" + name + "_out_dir",
        visibility = ["//visibility:public"],
    )
