#!/usr/bin/env python3
"""Compare public Cargo build scripts with the hermetic consumer adapters."""

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
RULES = HERE.parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bazel", default="bazel")
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument(
        "--macos-sdk",
        type=Path,
        help="Existing macos_sdk repository for Linux cross-builds",
    )
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error(
            "This fail/pass runner currently requires Linux; Apple targets are cross-compiled."
        )
    work = (
        args.work_dir or Path(tempfile.mkdtemp(prefix="rules-rs-bindgen-"))
    ).resolve()
    work.mkdir(parents=True, exist_ok=True)
    if work.is_relative_to(RULES):
        parser.error("Choose --work-dir outside the rules_rs checkout.")
    rules_snapshot = work / "rules_rs"
    # Keep local override inputs inside the workspace's visible /tmp subtree.
    shutil.copytree(
        RULES,
        rules_snapshot,
        dirs_exist_ok=True,
        ignore=shutil.ignore_patterns(".git", "bazel-*", "__pycache__"),
    )
    print(f"Evidence: {work}", flush=True)

    def run(variant, name, command, *, failure=None):
        flags = ["--color=no", "--curses=no", "--noshow_progress"]
        if sys.platform == "linux":
            flags += ["--host_platform=//:linux_host"]
        if args.macos_sdk:
            flags += [
                "--override_repository=llvm++osx+macos_sdk="
                + str(args.macos_sdk.resolve())
            ]
        result = subprocess.run(
            [args.bazel, "--ignore_all_rc_files", *command, *flags],
            cwd=work / variant,
            text=True,
            capture_output=True,
        )
        (work / f"{variant}-{name}.log").write_text(result.stdout + result.stderr)
        if failure:
            if result.returncode == 0 or failure not in result.stdout + result.stderr:
                raise RuntimeError(f"{variant}/{name}: expected {failure!r}; see log")
        elif result.returncode:
            raise RuntimeError(f"{variant}/{name}: exit {result.returncode}; see log")
        print(
            f"{variant}/{name}: {'expected libclang failure' if failure else 'PASS'}",
            flush=True,
        )
        return result.stdout

    for variant in ["baseline", "hermetic"]:
        directory = work / variant
        directory.mkdir(exist_ok=True)
        for name in [
            "BUILD.bazel",
            "Cargo.toml",
            "Cargo.lock",
            "lib.rs",
            "aic_runtime_test.rs",
            "aic_compile.rs",
            "netstat_compile.rs",
        ]:
            shutil.copyfile(HERE / name, directory / name)
        module = (
            (HERE / "MODULE.bazel")
            .read_text()
            .replace('path = "../.."', "path = " + json.dumps(str(rules_snapshot)))
        )
        if variant == "baseline":
            for crate in ["aic-sdk-sys", "netstat2"]:
                module += (
                    f'\ncrate.annotation(crate = "{crate}", gen_build_script = "on")\n'
                )
        else:
            for crate in ["aic-sdk-sys", "netstat2"]:
                snippet = crate + ".MODULE.bazel"
                shutil.copyfile(
                    RULES / "3rd_party" / crate / "include.MODULE.bazel",
                    directory / snippet,
                )
                module += f'\ninclude("//:{snippet}")\n'
        (directory / "MODULE.bazel").write_text(module)

    run(
        "baseline",
        "aic",
        ["test", "//:aic_runtime_test"],
        failure="Unable to find libclang",
    )
    run("baseline", "netstat-linux", ["build", "//:netstat_compile"])
    run("hermetic", "native", ["test", "//:aic_runtime_test", "//:netstat_compile"])

    actions = json.loads(
        run(
            "hermetic",
            "actions",
            [
                "aquery",
                'mnemonic("RustBindgen", deps(//:aic_runtime_test))',
                "--output=jsonproto",
            ],
        )
    )["actions"]
    counts = Counter(action["configurationId"] for action in actions)
    assert counts and all(count == 1 for count in counts.values()), (
        "AIC should generate bindings once per configuration"
    )

    output_base = subprocess.check_output(
        [args.bazel, "--ignore_all_rc_files", "info", "output_base"],
        cwd=work / "hermetic",
        text=True,
    ).strip()
    source = next(
        (Path(output_base) / "external").glob(
            "*crates__aic-sdk-sys-0.21.3/build-utils/runtime_linking.rs"
        )
    )
    generator = work / "hermetic" / "generator"
    generator.mkdir(exist_ok=True)
    shutil.copyfile(source, generator / "runtime_linking.rs")
    shutil.copyfile(
        HERE / "runtime_generator_test.rs", generator / "runtime_generator_test.rs"
    )
    shutil.copyfile(HERE / "generator.BUILD.bazel", generator / "BUILD.bazel")
    bindings = next(
        (Path(output_base) / "execroot" / "_main" / "bazel-out").glob(
            "*/bin/external/*crates__aic-sdk-sys-0.21.3/aic_bindings.rs",
        )
    )
    shutil.copyfile(bindings, generator / "aic_bindings.rs")
    run("hermetic", "runtime-generator", ["test", "//generator:runtime_generator_test"])

    if args.macos_sdk or sys.platform == "darwin":
        platform = "--platforms=@rules_rs//rs/platforms:aarch64-apple-darwin"
        run(
            "baseline",
            "netstat-apple",
            ["build", "//:netstat_compile", platform],
            failure="Unable to find libclang",
        )
        run(
            "hermetic",
            "apple",
            ["build", "//:netstat_compile", "//:aic_compile", platform],
        )


if __name__ == "__main__":
    main()
