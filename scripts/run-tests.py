#!/usr/bin/env python3
"""Universal test runner with auto-detection for multiple project types."""

import sys
import subprocess
from pathlib import Path


def find_projects(target: Path, maxdepth: int = 4) -> list[Path]:
    """Find all testable project directories within target."""
    markers = [
        "Makefile",
        "Cargo.toml",
        "package.json",
        "go.mod",
        "run_tests.sh",
        "test_*.py",
    ]
    projects: set[Path] = set()

    for depth in range(maxdepth + 1):
        if depth == 0:
            pattern = ""
        else:
            pattern = "/".join(["*"] * depth) + "/"

        for marker in markers:
            for path in target.glob(f"{pattern}{marker}"):
                if "/.git/" not in str(path) and "/." not in str(
                    path.relative_to(target)
                ):
                    projects.add(path.parent)

    return sorted(projects)


def run_tests(target: Path) -> int:
    """Detect project type and run appropriate tests."""

    if not target.is_dir():
        print(f"Error: Directory '{target}' does not exist.")
        return 1

    if (target / "Makefile").exists() and target.resolve() != Path.cwd():
        print(f"► [Recursive] Delegating to {target}/Makefile...")
        return subprocess.run(["make", "-C", str(target), "test"]).returncode

    if (target / "Cargo.toml").exists():
        print(f"► [Rust] Running tests in {target}")
        return subprocess.run(["cargo", "test"], cwd=target).returncode

    if (target / "package.json").exists():
        print(f"► [Node] Running tests in {target}")
        return subprocess.run(["npm", "test"], cwd=target).returncode

    if (target / "go.mod").exists():
        print(f"► [Go] Running tests in {target}")
        return subprocess.run(["go", "test", "./..."], cwd=target).returncode

    if (target / "run_tests.sh").exists():
        print(f"► [Script] Executing custom runner in {target}")
        return subprocess.run(["./run_tests.sh"], cwd=target).returncode

    if (target / "requirements.txt").exists() or any(target.glob("*.py")):
        print(f"► [Python] Running unittest in {target}")
        test_dir = target / "tests" if (target / "tests").is_dir() else target
        return subprocess.run(
            [
                "python3",
                "-m",
                "unittest",
                "discover",
                "-s",
                str(test_dir),
                "-p",
                "test_*.py",
                "-v",
            ]
        ).returncode

    projects = find_projects(target)

    if not projects:
        print(f"Error: No testable projects found in {target}")
        return 1

    for proj in projects:
        if proj == target or proj == Path("."):
            continue
        print()
        exit_code = run_tests(proj)
        if exit_code != 0:
            return exit_code

    return 0


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    sys.exit(run_tests(target))
