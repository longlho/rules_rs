# Bazel first-party packages with shared Cargo dependency resolution

This directory is a standalone Bazel module. Run commands from this directory:

```sh
bazel build //apps/demo //libs/...
bazel run //apps/demo -- 443
```

The app prints `Endpoint: http://localhost:443`. Passing `invalid` instead of
`443` prints a port validation error and exits with status 1.

```text
//apps/demo
    └── //libs/service
            ├── //libs/config ── @crates//:anyhow
            └── //libs/formatting
```

The app and all three libraries contain only Rust sources and `BUILD.bazel` files.
They do not need Cargo manifests or registration as Cargo workspace members.
Their first-party dependencies and direct external dependencies are explicit
Bazel labels.

`MODULE.bazel` configures Rust toolchains and uses `crate.from_cargo` to generate
`@crates` from the root `Cargo.toml` and `Cargo.lock`. The root is a virtual Cargo
workspace with a shared version catalog in `[workspace.dependencies]`.
`tools/deps` is its sole member and requests the external crates and features
needed by the Bazel targets. Cargo resolves that union into the committed
lockfile; entries in `[workspace.dependencies]` alone do not request resolution.
The resolver package's Rust source is empty and the app does not depend on it.

To add a first-party library, create its Rust sources and `BUILD.bazel`, then add
its label to its consumers. If it needs a new external crate or feature, declare
the version in the root catalog, request it in `tools/deps/Cargo.toml`, update
the lockfile with `cargo generate-lockfile`, and add the generated `@crates` label
to the library's `deps`.

The local override loads `rules_rs` from this checkout. In a separate repository,
replace it with a released `rules_rs` dependency. The configured platform triples
cover Linux and macOS hosts and targets; extend them for other platforms.
