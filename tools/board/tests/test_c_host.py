"""Compile the portable host with a deterministic wire-contract peer."""
import shutil
import subprocess
from pathlib import Path

import pytest


def test_c_host_wire_contract(tmp_path):
    cc = shutil.which("cc")
    if cc is None:
        pytest.fail("native C host checks require cc")
    source = Path(__file__).resolve().parents[1] / "c_host"
    harness = tmp_path / "harness.c"
    harness.write_text(r'''
#include "warp_host.h"
#include <assert.h>
#include <string.h>
typedef struct { size_t n; uint8_t tx[3], rx[3]; int fail; } step;
typedef struct { const step *steps; size_t count, index; } peer;
static int xfer(void *context, const uint8_t *tx, uint8_t *rx, size_t n) {
    peer *p = context;
    const step *s;
    assert(p->index < p->count);
    s = &p->steps[p->index++];
    assert(n == s->n && memcmp(tx, s->tx, n) == 0);
    memcpy(rx, s->rx, n);
    return s->fail;
}
int main(void) {
    const step writes[] = {
      {1,{1},{0x60},0}, {1,{1},{0x68},0}, {3,{0x30,0,0xa5},{0},0},
      {1,{1},{0x68},0}, {3,{0x30,1,0x5a},{0},0}};
    peer p = {writes,5,0}; warp_host h = {xfer,&p};
    const uint8_t data[] = {0xa5,0x5a}; size_t done = 77;
    uint8_t byte = 0xcc, status = 0, error = 0;
    assert(warp_channel_write_many(&h,data,2,1,2,&done)==WARP_OK);
    assert(done==2 && p.index==5);
    { const step reads[] = {{2,{0x31,0},{0x60,0xff},0},
                            {2,{0x31,0},{0x70,0x00},0},
                            {2,{0x31,0},{0x70,0x81},0}};
      uint8_t out[2]={0xaa,0xbb};
      p=(peer){reads,3,0};
      assert(warp_channel_read_many(&h,out,2,2,&done)==WARP_OK);
      assert(done==2 && out[0]==0 && out[1]==0x81 && p.index==3);
    }
    { const step full[]={{1,{1},{0x60},0},{1,{1},{0x60},0}};
      p=(peer){full,2,0};
      assert(warp_channel_write(&h,7,0,2)==WARP_TIMEOUT);
      assert(p.index==2);
    }
    { const step empty[]={{2,{0x31,0},{0x60,0xff},0}};
      p=(peer){empty,1,0};
      assert(warp_channel_read(&h,&byte,1)==WARP_TIMEOUT && byte==0xcc);
    }
    { const step stopped[]={{1,{1},{0x48},0},{2,{0x31,0},{0x50,9},0}};
      p=(peer){stopped,2,0};
      assert(warp_channel_write(&h,1,0,1)==WARP_STATE);
      assert(warp_channel_read(&h,&byte,1)==WARP_STATE && byte==0xcc);
    }
    { const step failed[]={{1,{1},{0},1}};
      p=(peer){failed,1,0};
      assert(warp_channel_write(&h,1,0,3)==WARP_IO && p.index==1);
    }
    { const step partial[]={{1,{1},{0x68},0},{3,{0x30,0,0xa5},{0},0},
                            {1,{1},{0x68},0},{3,{0x30,1,0x5a},{0},1}};
      p=(peer){partial,4,0};
      assert(warp_channel_write_many(&h,data,2,1,1,&done)==WARP_IO);
      assert(done==1 && p.index==4);
    }
    { const step partial_read[]={{2,{0x31,0},{0x70,0x42},0},
                                 {2,{0x31,0},{0x70,0x43},1}};
      uint8_t out[2]={0xaa,0xbb};
      p=(peer){partial_read,2,0};
      assert(warp_channel_read_many(&h,out,2,3,&done)==WARP_IO);
      assert(done==1 && out[0]==0x42 && out[1]==0xbb && p.index==2);
    }
    { const step status_steps[]={{1,{1},{0x67},0},
                                {3,{2,0,0},{0x67,0x65,0x12},0}};
      p=(peer){status_steps,2,0};
      assert(warp_poll(&h,&status)==WARP_OK && status==0x67);
      assert(warp_read_status(&h,&status,&error)==WARP_OK);
      assert(status==0x65 && error==0x12);
    }
    p=(peer){0,0,0};
    assert(warp_channel_read(&h,&byte,0)==WARP_TIMEOUT);
    assert(warp_channel_write(&h,0,0,0)==WARP_TIMEOUT);
    assert(warp_channel_write_many(&h,0,0,0,0,&done)==WARP_OK && done==0);
    assert(warp_channel_read_many(&h,0,0,0,&done)==WARP_OK && done==0);
    assert(warp_poll(0,&status)==WARP_ARGUMENT);
    assert(warp_channel_read(&h,0,1)==WARP_ARGUMENT);
    assert(warp_channel_write_many(&h,0,1,0,1,&done)==WARP_ARGUMENT && done==0);
    return 0;
}
''')
    executable = tmp_path / "host_test"
    subprocess.run([cc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-pedantic",
                    "-I", str(source), str(source / "warp_host.c"), str(harness),
                    "-o", str(executable)], check=True, capture_output=True, text=True)
    subprocess.run([str(executable)], check=True, capture_output=True, text=True)
