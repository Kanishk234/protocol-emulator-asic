"""Pin-frame assertions from PS/2's eleven-bit, LSB-first wire definition."""
from tripwire_spec import TAGS

TAG_DATA, TAG_ERR = TAGS['DATA'], TAGS['ERR']


def frame_word(byte, *, start_bad=False, parity_bad=False, stop_bad=False):
    parity=1-(byte.bit_count()&1)
    return int(start_bad) | byte<<1 | (parity^parity_bad)<<9 | int(not stop_bad)<<10


def token_for_word(word):
    data=word>>1 & 255
    framed=not word & 1 and bool(word & 0x400)
    odd=(data.bit_count()+(word>>9 & 1))&1
    return (TAG_DATA,data) if framed and odd else (TAG_ERR,word)


class FrameMonitor:
    def __init__(self,expected):
        self.expected=list(expected)
        self.previous_clk=1
        self.bits=[]
        self.frames=[]

    def sample(self,clk,data):
        if self.previous_clk and not clk:
            self.bits.append(data)
            if len(self.bits)==11:
                word=sum(b<<i for i,b in enumerate(self.bits))
                assert len(self.frames)<len(self.expected), 'Unexpected PS/2 frame'
                assert word==self.expected[len(self.frames)], 'PS/2 wire word differs from injected frame'
                self.frames.append(word)
                self.bits=[]
        self.previous_clk=clk

    def finish(self):
        assert not self.bits and self.frames==self.expected, 'Missing/truncated PS/2 frame'
        assert self.frames, 'No complete frame checked'
        return [token_for_word(word) for word in self.frames]
