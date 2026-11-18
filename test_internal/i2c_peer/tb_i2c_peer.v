// Verification-only connection of an independent controller to the chip's pads.
`default_nettype none
`timescale 1ns / 1ps
module tb_i2c_peer (
    input wire clk, rst_n, ena,
    input wire [7:0] ui_drv,
    input wire loop0,
    input wire [7:0] uio_in,
    output wire [7:0] ui_in, uo_out, uio_out, uio_oe, uio_bus,
    input wire [6:0] cmd_address,
    input wire cmd_start, cmd_read, cmd_write, cmd_write_multiple, cmd_stop, cmd_valid,
    output wire cmd_ready,
    input wire [7:0] data_in,
    input wire data_valid, data_last,
    output wire data_ready,
    output wire [7:0] data_out,
    output wire read_valid, read_last,
    input wire read_ready,
    input wire [15:0] prescale,
    output wire peer_busy, peer_bus_control, peer_bus_active, peer_missed_ack,
    output wire peer_scl_o, peer_scl_t, peer_sda_o, peer_sda_t
);
    wire [7:0] released = (~uio_oe | uio_out) & uio_in;
    assign uio_bus = {released[7:2],
                      released[1] & (peer_scl_t | peer_scl_o),
                      released[0] & (peer_sda_t | peer_sda_o)};
    tb_chip chip (
        .clk(clk), .rst_n(rst_n), .ena(ena), .ui_drv(ui_drv), .loop0(loop0),
        .uio_in(uio_bus), .ui_in(ui_in), .uo_out(uo_out), .uio_out(uio_out), .uio_oe(uio_oe)
    );
    i2c_master peer (
        .clk(clk), .rst(~rst_n),
        .s_axis_cmd_address(cmd_address), .s_axis_cmd_start(cmd_start),
        .s_axis_cmd_read(cmd_read), .s_axis_cmd_write(cmd_write),
        .s_axis_cmd_write_multiple(cmd_write_multiple), .s_axis_cmd_stop(cmd_stop),
        .s_axis_cmd_valid(cmd_valid), .s_axis_cmd_ready(cmd_ready),
        .s_axis_data_tdata(data_in), .s_axis_data_tvalid(data_valid),
        .s_axis_data_tready(data_ready), .s_axis_data_tlast(data_last),
        .m_axis_data_tdata(data_out), .m_axis_data_tvalid(read_valid),
        .m_axis_data_tready(read_ready), .m_axis_data_tlast(read_last),
        .scl_i(uio_bus[1]), .scl_o(peer_scl_o), .scl_t(peer_scl_t),
        .sda_i(uio_bus[0]), .sda_o(peer_sda_o), .sda_t(peer_sda_t),
        .busy(peer_busy), .bus_control(peer_bus_control),
        .bus_active(peer_bus_active), .missed_ack(peer_missed_ack),
        .prescale(prescale), .stop_on_idle(1'b0)
    );
endmodule
`default_nettype wire
