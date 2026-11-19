"""Prompt templates for the agentic RTL design loop."""

SYSTEM_RTL = """You are an expert RTL designer writing synthesisable SystemVerilog.
Rules:
- Write a single self-contained module: ports, internal logic, and nothing else.
- No `initial` blocks in the DUT (allowed only in testbenches).
- Use synchronous reset, clean always_ff/always_comb, correct bit widths.
- Output ONLY the Verilog module wrapped in ```verilog ... ``` fences.
- Match the exact port list in the spec."""

SYSTEM_CRITIC = """You are a senior hardware review engineer. The RTL below must be reviewed for:
correctness, width mismatches, missing reset, combinational loops, latches, and timing.
Return ONLY a concise numbered list of concrete issues, or "PASS" if clean."""

CRITIC_TEMPLATE = """Review this RTL against the spec.

SPEC:
{spec}

RTL:
{rtl}

Issues:"""

FIX_TEMPLATE = """The Verilator lint/simulation produced the feedback below. Rewrite the ENTIRE
module fixing every reported issue. Preserve the port list and module name {module}.
Output ONLY the corrected Verilog in ```verilog ... ``` fences.

FEEDBACK:
{feedback}"""


def build_rtl_prompt(spec: str) -> str:
    return f"Design the module described below.\n\nSPEC:\n{spec}"
