#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
fixture="${repo_root}/repro/external_manifest_repro/source"
repro_dir="$(mktemp -d)"
trap 'rm -rf "${repro_dir}"' EXIT

tar -czf "${repro_dir}/source.tar.gz" -C "${fixture}" .
archive_sha="$(sha256sum "${repro_dir}/source.tar.gz" | cut -d ' ' -f 1)"

cat > "${repro_dir}/MODULE.bazel" <<EOF
module(name = "external_manifest_repro")
bazel_dep(name = "rules_rs", version = "0.0.111")
local_path_override(module_name = "rules_rs", path = "${repo_root}")

http_archive = use_repo_rule("@bazel_tools//tools/build_defs/repo:http.bzl", "http_archive")
http_archive(
    name = "source",
    sha256 = "${archive_sha}",
    url = "file://${repro_dir}/source.tar.gz",
)

crate = use_extension("@rules_rs//rs:extensions.bzl", "crate")
crate.from_cargo(
    name = "external_crates",
    cargo_lock = "@source//:Cargo.lock",
    cargo_toml = "@source//:Cargo.toml",
    platform_triples = ["x86_64-unknown-linux-gnu"],
)
use_repo(crate, "external_crates")
EOF

touch "${repro_dir}/BUILD.bazel"
cd "${repro_dir}"
"${BAZEL_BIN:-bazel}" --output_user_root="${BAZEL_OUTPUT_USER_ROOT:-${repro_dir}/bazel-user-root}" query '@external_crates//:all' --output=label
