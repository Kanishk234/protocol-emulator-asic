// R4 spike (branch spike/r4-floorplan only): a routine sequencer stub for one lane, so the lane's
// routine port and the SRAM rotation (§6.2, §14 R1-R3) exist in the floorplan. It keeps RPC, fetches
// SRAM[RPC] into RIR on the lane's rotation slot while RB = 1, and loads RPC from the entry table after
// a CALL. Branches, DJNZ and LD/ST are not modelled (phase 2's trw_lane routine controller does them);
// the area here is a lower bound.
`default_nettype none

module r4_seq (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        run,
    input  wire        my_slot,     // this clock's SRAM access belongs to this lane
    input  wire        rb,
    input  wire        call_req,
    input  wire [4:0]  call_idx,
    input  wire        rt_take,
    input  wire [15:0] rdata,       // SRAM data, valid the clock after an access
    output wire        req_en,
    output wire [8:0]  req_addr,
    output reg         rir_valid,
    output reg  [15:0] rir
);
    reg [8:0] rpc;
    reg       pc_call;
    reg [4:0] cidx;
    reg [1:0] await_q;           // 1: an RIR fetch returns now, 2: an entry-table read returns now

    wire want_call  = pc_call;
    wire want_fetch = run && rb && !rir_valid && !pc_call && (await_q == 2'd0);
    assign req_en   = my_slot && (want_call || want_fetch);
    assign req_addr = want_call ? {4'd0, cidx} : rpc;

    always @(posedge clk) begin
        if (!rst_n) begin
            rpc <= 9'd0;  pc_call <= 1'b0;  cidx <= 5'd0;  await_q <= 2'd0;
            rir_valid <= 1'b0;  rir <= 16'd0;
        end else begin
            if (call_req) begin
                pc_call <= 1'b1;
                cidx    <= call_idx;
            end else if (my_slot && want_call) begin
                pc_call <= 1'b0;
            end
            await_q <= !req_en ? 2'd0 : want_call ? 2'd2 : 2'd1;
            if (await_q == 2'd1) begin
                rir       <= rdata;
                rir_valid <= 1'b1;
            end else if (rt_take) begin
                rir_valid <= 1'b0;
            end
            if (await_q == 2'd2)
                rpc <= rdata[8:0];
            else if (rt_take)
                rpc <= rpc + 9'd1;
        end
    end
endmodule
