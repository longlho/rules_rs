# Hermetic bindgen consumers

AIC and netstat2 invoke Cargo bindgen, which loads host libclang. These
adapters use rules_rs's existing prebuilt bindgen instead. AIC's build script
still handles SDK linking and runtime symbols; netstat2 receives Apple
`libproc_bindings.rs` through `BuildInfo.out_dir`.

## Standalone proof

From this checkout on Linux, with Python 3 and Bazel 9.2.0:

```sh
python3 examples/hermetic_bindgen_consumers/verify.py --bazel bazel
```

The runner creates isolated baseline and hermetic workspaces, ignoring ambient
Bazel configuration. Both set `LIBCLANG_PATH` to a nonexistent directory. This
makes the host dependency explicit even on machines with libclang installed.
Logs and generated files stay in the printed temporary directory; use
`--work-dir /tmp/bindgen-proof` to retain a chosen location.

The baseline uses unmodified public crates. The hermetic variant copies the
two `3rd_party/*/include.MODULE.bazel` snippets from this checkout unchanged.
No application checkout, private registry, native AIC SDK, or credentials
are required. AIC uses its public `runtime-linking` feature, without
`download-lib`.

Checks:

- Baseline AIC fails with `Unable to find libclang`.
- Baseline Linux netstat2 builds: its Linux implementation needs no bindings.
- Hermetic AIC compiles, links, and tests without host libclang or an AIC SDK.
  Its loader reports the expected error for an absent runtime library.
- AIC has exactly one `RustBindgen` action per tested configuration.
- Tests compile the actual patched runtime generator from the fetched crate.
  All 38 symbols survive; unrelated foreign functions, statics, and types stay
  in bindings. Repeated generation succeeds.

To also cross-build Apple consumers, supply an existing hermetic-llvm
`macos_sdk` repository containing `sysroot/`:

```sh
python3 examples/hermetic_bindgen_consumers/verify.py \
  --macos-sdk /path/to/macos_sdk
```

Baseline Apple netstat2 fails loading libclang. Both patched consumers
cross-compile for `aarch64-apple-darwin`. This checks compilation, not target
execution. Target SDK headers remain necessary; the patch removes the separate
host-libclang requirement. It does not fix native Xcode handling or provide
native AIC library packaging.

## Upstream status, checked 2026-10-27

This follows existing integrations: [AWS-LC #176](https://github.com/hermeticbuild/rules_rs/pull/176)
and [CoreAudio #178](https://github.com/hermeticbuild/rules_rs/pull/178) already
merged. The [CoreAudio discussion](https://github.com/hermeticbuild/rules_rs/pull/178#issuecomment-4950760991)
describes the same prebuilt-bindgen/cacheable-action approach. The
[prebuilt executable](https://github.com/hermeticbuild/bindgen#readme) embeds
libclang; [Cargo bindgen 0.72.1](https://github.com/rust-lang/rust-bindgen/blob/v0.72.1/bindgen/Cargo.toml)
defaults to dynamically loading it.

Upstream [main at 9148145](https://github.com/hermeticbuild/rules_rs/commit/9148145dc6e0999041e5968743c04f696e40c72c)
and latest release [v0.1.3](https://github.com/hermeticbuild/rules_rs/releases/tag/v0.1.3)
have generic bindgen support but no AIC/netstat2 adapters. Repository searches
found no matching crate-specific issue or PR.

Native Xcode placeholders remain a separate open
[issue #225](https://github.com/hermeticbuild/rules_rs/issues/225), with
[PR #179](https://github.com/hermeticbuild/rules_rs/pull/179) still open.
Linux cross-builds do not validate that path. Dev-only extension metadata
[#203](https://github.com/hermeticbuild/rules_rs/pull/203) is already fixed;
no workaround is included here.
