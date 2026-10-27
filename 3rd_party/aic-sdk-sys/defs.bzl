"""Hermetic AIC SDK binding generation; native linking stays in build.rs."""

load("@rules_cc//cc:defs.bzl", "cc_library")
load("@rules_rs//rs:rules_rust_bindgen.bzl", "rust_bindgen")

def aic_sdk_bindings(name, header, clang_flags = []):
    """Generates SDK bindings shared by link-time and runtime-loading builds."""
    cc_library(
        name = name + "_header",
        hdrs = [header],
    )
    flags = [
        "--constified-enum-module",
        "AicErrorCode",
        "--constified-enum-module",
        "AicProcessorParameter",
        "--constified-enum-module",
        "AicVadParameter",
    ]
    rust_bindgen(
        name = name,
        header = header,
        cc_lib = ":" + name + "_header",
        clang_flags = clang_flags,
        bindgen_flags = flags,
        visibility = ["//visibility:public"],
    )
