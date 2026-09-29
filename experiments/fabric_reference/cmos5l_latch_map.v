// Experimental mapping only. Positive-level latch in the pinned CMOS5L PDK.
module \$_DLATCH_P_ (input E, D, output Q);
    sg13cmos5l_dlhq_1 _TECHMAP_REPLACE_ (.GATE(E), .D(D), .Q(Q));
endmodule
