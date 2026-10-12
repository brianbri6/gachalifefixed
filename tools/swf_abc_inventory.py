#!/usr/bin/env python3
"""Inventory SWF tags and embedded AS3 DoABC blocks without external dependencies."""
from __future__ import annotations
import argparse,json,struct,zlib
from pathlib import Path

def load_swf(path:Path)->bytes:
    raw=path.read_bytes()
    if len(raw)<8: raise ValueError('SWF too small')
    sig=raw[:3]; declared=struct.unpack_from('<I',raw,4)[0]
    if sig==b'FWS': data=raw
    elif sig==b'CWS': data=raw[:8]+zlib.decompress(raw[8:])
    else: raise ValueError(f'Unsupported SWF signature {sig!r}')
    if len(data)!=declared: raise ValueError(f'Decompressed length {len(data)} != declared {declared}')
    return data

def rect_end_offset(data:bytes,start:int=8)->int:
    first=data[start]; nbits=first>>3; total_bits=5+nbits*4; return start+(total_bits+7)//8

def iter_tags(data:bytes):
    pos=rect_end_offset(data)+4
    while pos+2<=len(data):
        rec=struct.unpack_from('<H',data,pos)[0]; pos+=2; code=rec>>6; short_len=rec&0x3f
        if short_len==0x3f:
            if pos+4>len(data): raise ValueError('Truncated long tag length')
            length=struct.unpack_from('<I',data,pos)[0]; pos+=4
        else:length=short_len
        body_start=pos; body_end=pos+length
        if body_end>len(data): raise ValueError(f'Tag {code} overruns file')
        yield code,body_start,length,data[body_start:body_end]; pos=body_end
        if code==0:break

def parse_doabc(body:bytes):
    if len(body)<5:return None
    flags=struct.unpack_from('<I',body,0)[0]; nul=body.find(b'\x00',4)
    if nul<0:return None
    return flags,body[4:nul].decode('utf-8','replace'),body[nul+1:]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('swf',type=Path); ap.add_argument('--json',type=Path); args=ap.parse_args(); data=load_swf(args.swf); counts={}; abcs=[]
    for idx,(code,off,length,body) in enumerate(iter_tags(data)):
        counts[code]=counts.get(code,0)+1
        if code==82:
            parsed=parse_doabc(body)
            if parsed:
                flags,name,abc=parsed; abcs.append({'tag_index':idx,'offset':off,'tag_length':length,'flags':flags,'name':name,'abc_length':len(abc),'abc_hex_prefix':abc[:8].hex()})
    result={'file':str(args.swf),'size':args.swf.stat().st_size,'swf_version':data[3],'uncompressed_size':len(data),'tag_counts':counts,'doabc_count':len(abcs),'doabc':abcs}
    print(json.dumps(result,indent=2))
    if args.json: args.json.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
