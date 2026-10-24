"""Diagnostic R1 adapter for the unchanged production management shell.

Uses the frozen candidate pin map, not G1's fixed fabric cell numbering.
This simulation wrapper is not a replacement production top or physical macro.
"""
import csv
import re


def shell_wrapper(model):
    connections={}
    for row in csv.DictReader((model/'pins.csv').open()):
        pin=row['pin']; coordinate,letter=row['bel'].split('/')
        base=f'Tile_{coordinate}_{letter}_'
        if pin=='clk':signal='clk'
        elif pin=='rst_n':signal='user_rst_n'
        elif pin.startswith('FAB_IN'):signal=f"fab_in[{int(pin[6:])}]"
        elif pin.startswith('FAB_OUT'):signal=f"fab_out[{int(pin[7:])}]"
        elif pin.startswith('FAB_IO'):
            bit=int(pin[6:])
            for suffix,signal in [('OUT_top',f'io_in[{bit}]'),('IN_top',f'io_out[{bit}]'),('EN_top',f'io_oe[{bit}]')]:
                connections[base+suffix]=signal
            continue
        elif pin.startswith('h_'):signal=pin
        else:raise ValueError('Unknown candidate pin: '+pin)
        suffix={'in':'OUT_top','clock':'OUT_top','out':'IN_top','out_en':'EN_top'}[row['direction']]
        connections[base+suffix]=signal
    ports=set(re.findall(r'\binput\s+(?:wire\s+)?(?:\[[^\]]+\]\s*)?(Tile_\w+)',(model/'fabric.v').read_text()))
    reset='Tile_X0Y4_SYS_RESET_RESET_top'
    if reset not in ports:raise ValueError('Missing candidate auxiliary reset')
    connections[reset]='user_reset'
    for port in ports:connections.setdefault(port,"1'b0")
    source='''`timescale 1ns/1ps
`default_nettype none
module r1_tb(input wire clk, rst_n, ena,
input wire [7:0] ui_in, uio_in,
output wire [7:0] uo_out, uio_out, uio_oe);
reg [1:0] rst_sync;
reg rst_cfg_n;
always @(posedge clk) begin
    rst_sync <= {rst_sync[0],rst_n};
    rst_cfg_n <= rst_sync[1];
end
wire rst_s_n=rst_sync[1];
wire host_miso,host_irq,running,user_reset;
wire [31:0] cfg_word;
wire cfg_strobe,cfg_restart;
wire [7:0] h_wdata,h_rdata,h_status;
wire h_wlast,h_wvalid,h_wready,h_rvalid,h_rready,h_attention;
wp_shell #(.ARCH_VERSION(16'h00fe)) shell(
.clk(clk),.rst_n(rst_s_n),.host_cs_n(ui_in[0]),.host_sck(ui_in[1]),
.host_mosi(ui_in[2]),.host_miso(host_miso),.host_irq(host_irq),
.cfg_word(cfg_word),.cfg_strobe(cfg_strobe),.cfg_restart(cfg_restart),
.running(running),.user_reset(user_reset),
.h_wdata(h_wdata),.h_wlast(h_wlast),.h_wvalid(h_wvalid),.h_wready(h_wready),
.h_rdata(h_rdata),.h_rvalid(h_rvalid),.h_rready(h_rready),
.h_status(h_status),.h_attention(h_attention));
wire [159:0] frame_data,frame_strobe;
wp_fabric_cfg #(.ROWS(5),.COLS(8)) loader(
.clk(clk),.rst_n(rst_cfg_n),.word(cfg_word),.word_strobe(cfg_strobe),
.restart(cfg_restart),.frame_data(frame_data),.frame_strobe(frame_strobe));
wire [4:0] fab_in;
wire [7:0] io_in,io_out,io_oe;
wire [5:0] fab_out;
wp_sync #(.WIDTH(13)) input_sync(
.clk(clk),.rst_n(rst_s_n),.d({ui_in[7:3],uio_in}),.q({fab_in,io_in}));
reg user_rst_n;
reg [5:0] out_q;
reg [7:0] io_out_q,io_oe_q;
always @(posedge clk) begin
    if (!rst_s_n) begin
        user_rst_n<=1'b0;out_q<=6'b0;io_out_q<=8'b0;io_oe_q<=8'b0;
    end else begin
        user_rst_n<=!user_reset;
        out_q<=fab_out;io_out_q<=io_out;io_oe_q<=io_oe;
    end
end
assign uo_out={out_q & {6{running}},host_irq,host_miso};
assign uio_out=io_out_q & {8{running}};
assign uio_oe=io_oe_q & {8{running}};
eFPGA fabric(
'''
    items=[f'.{port}({signal})' for port,signal in sorted(connections.items())]
    items+=['.FrameData(frame_data)','.FrameStrobe(frame_strobe)']
    return source+',\n'.join(items)+');\nendmodule\n',sorted(ports)
