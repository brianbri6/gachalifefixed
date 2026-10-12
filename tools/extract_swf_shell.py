#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, struct, zlib
from pathlib import Path

def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def load_uncompressed(path: Path):
    raw=path.read_bytes(); sig=raw[:3]; ver=raw[3]; declared=struct.unpack_from('<I',raw,4)[0]
    if sig==b'FWS': body=raw[8:]
    elif sig==b'CWS': body=zlib.decompress(raw[8:])
    else: raise ValueError(f'unsupported SWF signature {sig!r}')
    data=b'FWS'+bytes([ver])+struct.pack('<I',declared)+body
    if len(data)!=declared: raise ValueError(f'decompressed size {len(data)} != declared {declared}')
    return raw,data,sig.decode('ascii')

def rect_end(data: bytes)->int:
    nbits=data[8]>>3
    return 8+(5+4*nbits+7)//8

def tags(data: bytes):
    pos=rect_end(data)+4; idx=0
    while pos+2<=len(data):
        rec_start=pos
        rec=struct.unpack_from('<H',data,pos)[0]; pos+=2
        code=rec>>6; sl=rec&0x3f
        if sl==0x3f:
            length=struct.unpack_from('<I',data,pos)[0]; pos+=4
        else: length=sl
        body_start=pos; end=pos+length
        if end>len(data): raise ValueError('tag overrun')
        yield idx,code,rec_start,body_start,end
        pos=end; idx+=1
        if code==0: break

def parse_doabc(body: bytes):
    flags=struct.unpack_from('<I',body,0)[0]
    nul=body.find(b'\0',4)
    if nul<0: raise ValueError('DoABC name terminator missing')
    return flags,body[4:nul].decode('utf-8','replace'),body[nul+1:]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('swf',type=Path,nargs='?',default=Path('/mnt/data/gacha-recovery/GachaLifePC.swf'))
    ap.add_argument('-o','--output',type=Path,default=Path(__file__).resolve().parent.parent/'swf_shell')
    a=ap.parse_args(); a.output.mkdir(parents=True,exist_ok=True)
    raw,data,input_sig=load_uncompressed(a.swf)
    do=[t for t in tags(data) if t[1]==82]
    if len(do)!=1: raise SystemExit(f'expected exactly one DoABC tag, got {len(do)}')
    idx,code,rec_start,body_start,end=do[0]
    flags,name,abc=parse_doabc(data[body_start:end])
    prefix=data[:rec_start]; suffix=data[end:]
    doabc_record=data[rec_start:end]
    (a.output/'prefix.fws.bin.z').write_bytes(zlib.compress(prefix,9))
    (a.output/'suffix.fws.bin.z').write_bytes(zlib.compress(suffix,9))
    (a.output/'original_doabc.tag.z').write_bytes(zlib.compress(doabc_record,9))
    (a.output/'original.abc.z').write_bytes(zlib.compress(abc,9))
    manifest={
      'source_swf':str(a.swf), 'source_sha256':sha256(raw), 'source_signature':input_sig,
      'swf_version':data[3], 'uncompressed_size':len(data), 'uncompressed_sha256':sha256(data),
      'doabc_tag_index':idx, 'doabc_record_offset':rec_start, 'doabc_record_length':len(doabc_record),
      'doabc_flags':flags, 'doabc_name':name, 'abc_length':len(abc), 'abc_sha256':sha256(abc),
      'prefix_length':len(prefix), 'prefix_sha256':sha256(prefix),
      'suffix_length':len(suffix), 'suffix_sha256':sha256(suffix),
      'tag_count':sum(1 for _ in tags(data)),
      'format':'zlib-compressed FWS prefix + complete DoABC record + FWS suffix'
    }
    (a.output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    (a.output/'README.md').write_text('''# Lossless SWF asset/timeline shell\n\nThis directory preserves the playable Gacha Life PC SWF around its single ActionScript `DoABC` tag. `prefix.fws.bin.z` and `suffix.fws.bin.z` contain every non-code SWF tag byte exactly as present after decompression, including shapes, sprites, bitmaps, sounds, fonts, timeline placements, frame labels, symbol linkage, and metadata. `original_doabc.tag.z` preserves the original bytecode tag and `original.abc.z` exposes its ABC payload separately.\n\nRun `python tools/rebuild_swf_shell.py` to reconstruct a playable SWF and verify its uncompressed SHA-256. A future compiler/ABC assembler can replace only the `DoABC` record while keeping the original asset/timeline shell unchanged.\n''',encoding='utf-8')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__': main()
