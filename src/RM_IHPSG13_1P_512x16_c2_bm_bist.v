// Port-only blackbox of the IHP 512x16 SRAM macro, for synthesis and lint.
// It is the MACROS "nl" entry in src/config.json and is NOT listed in info.yaml source_files: the
// hard macro comes from its GDS/LEF/LIB (MACROS), and simulation uses the vendored model in
// macro/RM_IHPSG13_1P_512x16_c2_bm_bist/. Do not give it a body (synthesis would build the RAM
// from flops). Port list copied from the vendored model; keep them identical.
// Same arrangement as tt_um_urish_sram_test and the Loom entry's sram-smoke branch.
`default_nettype none

/* verilator lint_off UNUSEDSIGNAL */
/* verilator lint_off UNDRIVEN */
module RM_IHPSG13_1P_512x16_c2_bm_bist (
    input  wire        A_CLK,
    input  wire        A_MEN,
    input  wire        A_WEN,
    input  wire        A_REN,
    input  wire [8:0]  A_ADDR,
    input  wire [15:0] A_DIN,
    input  wire        A_DLY,
    output wire [15:0] A_DOUT,
    input  wire [15:0] A_BM,
    input  wire        A_BIST_CLK,
    input  wire        A_BIST_EN,
    input  wire        A_BIST_MEN,
    input  wire        A_BIST_WEN,
    input  wire        A_BIST_REN,
    input  wire [8:0]  A_BIST_ADDR,
    input  wire [15:0] A_BIST_DIN,
    input  wire [15:0] A_BIST_BM
);
endmodule
/* verilator lint_on UNDRIVEN */
/* verilator lint_on UNUSEDSIGNAL */
