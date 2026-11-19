module tb_fifo;
  parameter WIDTH = 8;
  parameter DEPTH = 16;

  logic clk;
  logic rst_n;
  logic wr_en;
  logic [WIDTH-1:0] din;
  logic rd_en;
  logic [WIDTH-1:0] dout;
  logic full;
  logic empty;
  logic [$clog2(DEPTH):0] count;

  fifo #(.WIDTH(WIDTH), .DEPTH(DEPTH)) dut (
    .clk(clk), .rst_n(rst_n), .wr_en(wr_en), .din(din),
    .rd_en(rd_en), .dout(dout), .full(full), .empty(empty), .count(count)
  );

  initial begin
    clk = 0;
    forever #5 clk = ~clk;
  end

  int errors = 0;

  task check(input string name, input logic cond);
    if (!cond) begin
      $display("FAIL: %s", name);
      errors = errors + 1;
    end else begin
      $display("PASS: %s", name);
    end
  endtask

  initial begin
    rst_n = 0;
    wr_en = 0;
    rd_en = 0;
    din = 0;
    repeat (3) @(posedge clk);
    rst_n = 1;
    @(posedge clk);

    // Expect empty on reset
    check("empty_after_reset", empty === 1);
    check("count_zero", count === 0);

    // Fill FIFO completely; check not-full before each write except the last
    for (int i = 0; i < DEPTH; i++) begin
      check($sformatf("not_full_when_writing_%0d", i), (full === 0) || (i == DEPTH-1));
      wr_en = 1;
      din = i;
      @(posedge clk);
    end
    wr_en = 0;
    @(posedge clk);
    check("full_when_filled", full === 1);
    check("count_full", count === DEPTH);

    // Write when full must be ignored
    wr_en = 1;
    din = 8'hAB;
    @(posedge clk);
    wr_en = 0;
    @(posedge clk);
    check("count_still_full", count === DEPTH);

    // Drain FIFO; combinational dout shows mem[rd_ptr], valid before the
    // read edge that advances the pointer
    for (int i = 0; i < DEPTH; i++) begin
      check($sformatf("data_out_%0d", i), dout === i);
      rd_en = 1;
      @(posedge clk);
    end
    rd_en = 0;
    @(posedge clk);
    check("empty_after_drain", empty === 1);
    check("count_zero_final", count === 0);

    if (errors == 0) $display("ALL TESTS PASSED");
    else $display("%0d TESTS FAILED", errors);
    $finish;
  end

  // Timeout guard
  initial begin
    #1000;
    $display("TIMEOUT");
    $finish;
  end
endmodule
