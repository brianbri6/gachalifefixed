#!/usr/bin/env python3
"""Validate binary-derived recovery artifacts against the authoritative SWF."""
from __future__ import annotations
import argparse, hashlib, json, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent; sys.path.insert(0,str(HERE))
from abc_index import ABC, swf_abc
from avm2_disasm import decode
from avm2_to_as3_state import emit_method

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--manifest',type=Path,default=ROOT/'recovery_manifest.json'); ap.add_argument('--swf',type=Path,default=Path('/mnt/data/gacha-recovery/GachaLifePC.swf')); ap.add_argument('--skip-regenerate',action='store_true'); args=ap.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding='utf-8')); expected_hash=manifest['binary']['sha256']; actual_hash=hashlib.sha256(args.swf.read_bytes()).hexdigest(); errors=[]
    if actual_hash!=expected_hash: errors.append(f'SWF sha256 mismatch: expected {expected_hash}, got {actual_hash}')
    abc=ABC(swf_abc(args.swf)); name_map=abc.method_name_map(); checked=0
    for rec in manifest['recoveries']:
        mid=rec['binary_method_id']; label=f"{rec['source_class']}::{rec['method']} [method {mid}]"
        if mid not in abc.bodies: errors.append(f'{label}: method body missing'); continue
        aliases=name_map.get(mid,[]); expected_alias=f"{rec['binary_class']}::{rec['method']}"
        alias_ok=expected_alias in aliases or any(a.startswith(rec['binary_class']+'::') and a.split('::',1)[1].split('.')[-1]==rec['method'] for a in aliases)
        if not alias_ok: errors.append(f'{label}: expected method {rec["method"]!r} in {rec["binary_class"]!r}, got {aliases!r}')
        body=abc.bodies[mid]
        if len(body['code'])!=rec['bytecode_length']: errors.append(f"{label}: bytecode length {len(body['code'])} != {rec['bytecode_length']}")
        instruction_count=len(decode(abc,body['code']))
        if instruction_count!=rec['instruction_count']: errors.append(f"{label}: instruction count {instruction_count} != {rec['instruction_count']}")
        generated=ROOT/rec['generated_body']
        if not generated.exists(): errors.append(f'{label}: missing {generated.relative_to(ROOT)}'); continue
        text=generated.read_text(encoding='utf-8')
        if 'IllegalOperationError' in text or 'Not decompiled due' in text: errors.append(f'{label}: generated body still contains decompiler-error stub text')
        if text.count('{')!=text.count('}'): errors.append(f'{label}: braces are unbalanced')
        if not text.rstrip().endswith('}'): errors.append(f'{label}: generated method does not end with a closing brace')
        if not args.skip_regenerate:
            visibility='internal' if rec['source_signature'].lstrip().startswith('function ') else 'public'; fresh=emit_method(abc,mid,method_name=rec['method'],visibility=visibility)
            if fresh!=text: errors.append(f'{label}: generated file differs from deterministic regeneration')
        checked+=1
    print(f'validated {checked}/{len(manifest["recoveries"])} recovery methods'); print(f'SWF sha256 {actual_hash}')
    if errors:
        print(f'FAILED with {len(errors)} issue(s):',file=sys.stderr)
        for e in errors: print(f' - {e}',file=sys.stderr)
        return 1
    print('PASS: manifest, binary method mappings, instruction counts, and generated artifacts agree'); return 0
if __name__=='__main__': raise SystemExit(main())
