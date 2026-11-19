module fifo #(
  parameter WIDTH = 8,
  parameter DEPTH = 16
)(
  input  logic clk,
  input  logic rst_n,
  input  logic wr_en,
  input  logic [WIDTH-1:0] din,
  input  logic rd_en,
  output logic [WIDTH-1:0] dout,
  output logic full,
  output logic empty,
  output logic [$clog2(DEPTH):0] count
);
  localparam PTR_W = $clog2(DEPTH) + 1;
  logic [PTR_W-1:0] wr_ptr, rd_ptr;
  logic [WIDTH-1:0] mem [DEPTH];

  assign full  = (wr_ptr == {~rd_ptr[PTR_W-1], rd_ptr[PTR_W-2:0]});
  assign empty = (wr_ptr == rd_ptr);
  assign count = wr_ptr - rd_ptr;

  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) begin
      wr_ptr <= '0;
      rd_ptr <= '0;
    end else begin
      if (wr_en && !full) begin
        mem[wr_ptr[PTR_W-2:0]] <= din;
        wr_ptr <= wr_ptr + 1'b1;
      end
      if (rd_en && !empty) begin
        rd_ptr <= rd_ptr + 1'b1;
      end
    end
  end

  assign dout = mem[rd_ptr[PTR_W-2:0]];
endmodule
