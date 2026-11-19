"""Verilator tool-loop wrappers: lint and simulate generated RTL."""
import re
import shlex
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ToolResult:
    ok: bool
    output: str
    errors: list[str] = field(default_factory=list)


def _run(cmd: list[str], cwd: Path, timeout: int = 120) -> ToolResult:
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = proc.stdout + proc.stderr
        ok = proc.returncode == 0
    except subprocess.TimeoutExpired:
        return ToolResult(ok=False, output="timeout", errors=["timeout"])
    except FileNotFoundError:
        return ToolResult(
            ok=False,
            output="verilator not found; run: brew install verilator",
            errors=["verilator missing"],
        )
    errors = [l for l in output.splitlines() if re.search(r"%?Error|error", l, re.I)]
    return ToolResult(ok=ok, output=output, errors=errors)


def lint(rtl_dir: Path, top: str) -> ToolResult:
    """Run Verilator in lint-only mode over all .sv/.v in rtl_dir."""
    sources = sorted(list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")))
    if not sources:
        return ToolResult(ok=False, output="no RTL sources found", errors=["no sources"])
    args = [str(s.resolve()) for s in sources]
    return _run(
        ["verilator", "--lint-only", "--timing", "-Wall", "-Wno-fatal", "-Wno-DECLFILENAME",
         "--top-module", top, *args],
        cwd=rtl_dir.resolve(),
    )


def simulate(
    rtl_dir: Path,
    top: str,
    tb_file: Path,
    work_dir: Path,
    tb_top: str = "tb_top",
    timeout: int = 120,
) -> ToolResult:
    """Compile RTL + testbench with Verilator and run simulation.

    Runs in a space-free temp dir because Verilator's generated Makefile
    cannot handle spaces in paths (e.g. a workspace named "Default Project").
    """
    sources = sorted(list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")))
    if not sources:
        return ToolResult(ok=False, output="no RTL sources found", errors=["no sources"])

    with tempfile.TemporaryDirectory(prefix="vlsim_") as tmp:
        tmp_path = Path(tmp)
        for s in sources:
            shutil.copy2(s, tmp_path / s.name)
        shutil.copy2(tb_file, tmp_path / tb_file.name)
        src = " ".join(shlex.quote(s.name) for s in sources)
        tb = shlex.quote(tb_file.name)
        work = "build"
        cmd = (
            f"verilator --binary --timing -Wno-fatal -Wno-DECLFILENAME "
            f"--top-module {tb_top} {src} {tb} --Mdir {work} && "
            f"{work}/V{tb_top}"
        )
        return _run(["bash", "-c", cmd], cwd=tmp_path, timeout=timeout)


def extract_feedback(result: ToolResult, max_lines: int = 40) -> str:
    """Trim tool output into a concise feedback message for the LLM."""
    lines = result.output.splitlines()
    relevant = [l for l in lines if re.search(r"error|Error|FAILED|warning", l)]
    if not relevant:
        relevant = lines
    body = "\n".join(relevant[:max_lines])
    return f"tool_ok={result.ok}\n" + (body or result.output[:400])
