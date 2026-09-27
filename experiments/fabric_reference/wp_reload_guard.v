`default_nettype none
// Experimental management sequencer, not the production host/checksum block.
// image_valid must come from a trusted complete-image validator.
module wp_reload_guard (
    input wire clk,
    input wire rst_n,
    input wire begin_load,
    input wire abort_load,
    input wire commit_image,
    input wire image_valid,
    input wire write_active,
    output wire hold_fabric,
    output wire park_outputs,
    output wire user_reset,
    output wire load_allowed,
    output wire ready
);
    localparam [3:0] SAFE=0, ARM=1, LOAD=2, SETTLE0=3, SETTLE1=4,
                     RESET0=5, RESET1=6, RESET2=7, RESET3=8, RELEASE=9, RUN=10;
    reg [3:0] state;
    assign ready = state == RUN;
    assign load_allowed = state == LOAD;
    assign hold_fabric = !(state >= RESET0 && state <= RUN);
    assign park_outputs = !ready;
    assign user_reset = !ready;
    always @(posedge clk) begin
        if (!rst_n) state <= SAFE;
        else if (abort_load) state <= SAFE;
        else if (begin_load) state <= ARM;
        else case (state)
            SAFE: state <= SAFE;
            ARM: state <= LOAD;
            LOAD: if (commit_image && image_valid && !write_active) state <= SETTLE0;
            SETTLE0: state <= SETTLE1;
            SETTLE1: state <= RESET0;
            RESET0: state <= RESET1;
            RESET1: state <= RESET2;
            RESET2: state <= RESET3;
            RESET3: state <= RELEASE;
            RELEASE: state <= RUN;
            RUN: state <= RUN;
            default: state <= SAFE;
        endcase
    end
endmodule
`resetall
