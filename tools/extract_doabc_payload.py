#!/usr/bin/env python3
from __future__ import annotations
import argparse, struct, zlib
from pathlib import Path

def load(path:Path)->bytes:
    raw=path.read_bytes()
    if raw[:3]==b'CWS': return raw[:8]+zlib.decompress(raw[8:])
    if raw[:3]==b'FWS': return raw
    raise ValueError(raw[:3])

def rect_end(data):
    nbits=data[8]>>3
    return 8+(5+4*nbits+7)//8

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('swf',type=Path); ap.add_argument('-o','--output',type=Path,required=True); a=ap.parse_args()
    data=load(a.swf); p=rect_end(data)+4; found=[]
    while p+2<=len(data):
        rec=struct.unpack_from('<H',data,p)[0]; p+=2; code=rec>>6; ln=rec&63
        if ln==63: ln=struct.unpack_from('<I',data,p)[0]; p+=4
        body=data[p:p+ln]; p+=ln
        if code==82:
            nul=body.find(b'\0',4)
            if nul<0: raise ValueError('bad DoABC')
            found.append(body[nul+1:])
        if code==0: break
    if len(found)!=1: raise SystemExit(f'expected exactly one DoABC payload, got {len(found)}')
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(found[0]); print(f'wrote {a.output} bytes={len(found[0])}')
if __name__=='__main__': main()
