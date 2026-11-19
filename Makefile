.PHONY: demo lint sim clean

demo:
	python3 agent.py specs/fifo.txt

lint:
	verilator --lint-only --timing -Wall -Wno-fatal -Wno-DECLFILENAME rtl/*.sv

sim:
	verilator --binary --timing -Wno-fatal -Wno-DECLFILENAME --top-module tb_fifo rtl/*.sv tb/tb_fifo.sv --Mdir build && ./build/Vtb_fifo

clean:
	rm -rf rtl build sim obj_dir
