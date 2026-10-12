#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, struct, zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent

def sha(b): return hashlib.sha256(b).hexdigest()

def encode_tag(code:int, body:bytes)->bytes:
    n=len(body)
    if n<0x3f: return struct.pack('<H',(code<<6)|n)+body
    return struct.pack('<H',(code<<6)|0x3f)+struct.pack('<I',n)+body

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--shell',type=Path,default=ROOT/'swf_shell')
    ap.add_argument('--abc',type=Path,help='raw ABC payload to insert instead of the original DoABC tag')
    ap.add_argument('-o','--output',type=Path,default=ROOT/'build/GachaLifePC-rebuilt.swf')
    ap.add_argument('--fws',action='store_true',help='write uncompressed FWS instead of compressed CWS')
    a=ap.parse_args(); m=json.loads((a.shell/'manifest.json').read_text())
    prefix=zlib.decompress((a.shell/'prefix.fws.bin.z').read_bytes())
    suffix=zlib.decompress((a.shell/'suffix.fws.bin.z').read_bytes())
    if sha(prefix)!=m['prefix_sha256'] or sha(suffix)!=m['suffix_sha256']: raise SystemExit('shell chunk hash mismatch')
    if a.abc:
        abc=a.abc.read_bytes(); body=struct.pack('<I',m['doabc_flags'])+m['doabc_name'].encode()+b'\0'+abc; record=encode_tag(82,body)
    else: record=zlib.decompress((a.shell/'original_doabc.tag.z').read_bytes())
    data=bytearray(prefix+record+suffix); data[:3]=b'FWS'; struct.pack_into('<I',data,4,len(data))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    if a.fws: out=bytes(data)
    else: out=b'CWS'+bytes([data[3]])+struct.pack('<I',len(data))+zlib.compress(bytes(data[8:]),9)
    a.output.write_bytes(out)
    print(f'wrote {a.output} bytes={len(out)} sha256={sha(out)}'); print(f'uncompressed_sha256={sha(bytes(data))}')
    if not a.abc:
        if sha(bytes(data))!=m['uncompressed_sha256']: raise SystemExit('baseline rebuild differs from authoritative uncompressed SWF')
        print('PASS: baseline rebuild is byte-identical after SWF decompression')

if __name__=='__main__': main()
