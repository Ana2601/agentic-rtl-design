"""Agentic RTL design orchestrator.

Loop:
  1. LLM generates SystemVerilog from a spec (tools + critic pass).
  2. Verilator lint runs; errors feed back into the fix loop.
  3. On lint pass, Verilator simulation runs against the testbench.
  4. If sim passes, write the final RTL to rtl/ and report.
"""
import argparse
import re
import sys
from pathlib import Path

from llm import LLMClient
from prompts import CRITIC_TEMPLATE, FIX_TEMPLATE, SYSTEM_CRITIC, SYSTEM_RTL, build_rtl_prompt
from tools import extract_feedback, lint, simulate

FENCE = re.compile(r"```(?:verilog|systemverilog|sv)?\s*\n(.*?)```", re.DOTALL)


def extract_verilog(text: str) -> str:
    m = FENCE.search(text)
    if m:
        return m.group(1).strip()
    # Fall back to first `module` .. `endmodule`
    m2 = re.search(r"(module\s+.*?endmodule)", text, re.DOTALL)
    return m2.group(1).strip() if m2 else ""


def module_name(rtl: str) -> str:
    m = re.search(r"module\s+(\w+)", rtl)
    return m.group(1) if m else "top"


def main(spec_path: str, out_dir: str = "rtl", max_iter: int = 6) -> int:
    spec = Path(spec_path).read_text()
    llm = LLMClient()
    out = Path(out_dir)
    out.mkdir(exist_ok=True)
    rtl_dir = Path(".")

    rtl = extract_verilog(llm.chat(SYSTEM_RTL, build_rtl_prompt(spec)))
    if not rtl:
        print("!! LLM returned no Verilog", file=sys.stderr)
        return 1

    module = module_name(rtl)
    print(f"[*] module: {module}")

    for i in range(max_iter):
        print(f"[*] iter {i+1}: lint")
        rtl_path = out / f"{module}.sv"
        rtl_path.write_text(rtl + "\n")
        res = lint(out, module)

        if res.ok:
            print("[+] lint PASS")
            tb = find_testbench(spec_path, module)
            if tb:
                sim_res = simulate(out, module, tb, out / "sim", tb_top=f"tb_{module}")
                if sim_res.ok:
                    print("[+] SIM PASS")
                    print("[+] FINAL RTL written to", rtl_path)
                    return 0
                feedback = extract_feedback(sim_res)
            else:
                print("[*] no testbench found; skipping simulation")
                print("[+] FINAL RTL written to", rtl_path)
                return 0
        else:
            feedback = extract_feedback(res)

        critic = llm.critique(SYSTEM_CRITIC, CRITIC_TEMPLATE.format(spec=spec, rtl=rtl))
        rtl = extract_verilog(
            llm.chat(SYSTEM_RTL, FIX_TEMPLATE.format(module=module, feedback=feedback + "\n\nCRITIC:\n" + critic))
        )
        if not rtl:
            print("!! LLM produced empty RTL; stopping", file=sys.stderr)
            return 1

    print("[x] max iterations reached without passing")
    return 1


def find_testbench(spec_path: Path, module: str) -> Path | None:
    tb = Path("tb") / f"tb_{module}.sv"
    return tb if tb.exists() else None


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Agentic RTL design loop")
    p.add_argument("spec", help="path to spec file")
    p.add_argument("--out", default="rtl", help="output dir for generated RTL")
    p.add_argument("--max-iter", type=int, default=int(__import__("os").environ.get("MAX_ITER", 6)))
    args = p.parse_args()
    sys.exit(main(args.spec, args.out, args.max_iter))
