#!/usr/bin/env python3
"""Independently validate the four verified Gacha Life AVM2 fixes."""
from __future__ import annotations
import argparse, sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from abc_index import ABC, swf_abc
from avm2_disasm import decode

OWNER='GachaLifePC_fla.MainTimeline'

def pname(abc,mi):
    d=abc.multinames[mi]
    return abc.s(d.get('name',0)) if d else ''

def method_id(abc,name):
    hits=[]
    for mid,names in abc.method_name_map().items():
        if OWNER+'::'+name in names: hits.append(mid)
    if len(hits)!=1: raise AssertionError(f'{name}: expected one method, got {hits}')
    return hits[0]

def load(path:Path)->ABC:
    if path.suffix.lower()=='.swf': return ABC(swf_abc(path))
    return ABC(path.read_bytes())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input',type=Path,nargs='?',default=Path(__file__).resolve().parent.parent/'build/GachaLifePC-safe-patched-all4.swf')
    a=ap.parse_args(); abc=load(a.input); checks=[]
    ins=decode(abc,abc.bodies[method_id(abc,'generateRandomString')]['code']); by={x['offset']:x for x in ins}
    checks.append(('generateRandomString range', by.get(58,{}).get('name')=='nop'))
    ins=decode(abc,abc.bodies[method_id(abc,'minigameloop2')]['code']); by={x['offset']:x for x in ins}
    checks.append(('minigame2 cleanup receiver', by.get(1999,{}).get('name')=='getlocal0' and by.get(2000,{}).get('name')=='nop' and by.get(2001,{}).get('name')=='nop'))
    ins=decode(abc,abc.bodies[method_id(abc,'addComma')]['code']); by={x['offset']:x for x in ins}
    checks.append(('addComma zero guard', by.get(12,{}).get('name')=='getlocal1' and by.get(15,{}).get('name')=='ifne' and by.get(15,{}).get('targets')==[26] and by.get(22,{}).get('name')=='returnvalue'))
    body=abc.bodies[method_id(abc,'minigameloop6')]; ins=decode(abc,body['code']); by={x['offset']:x for x in ins}
    seq=[x for x in ins if 1902<=x['offset']<1918]; seq_names=[x['name'] for x in seq]
    handler_ok=len(seq)>=6 and seq[4]['name']=='getproperty' and pname(abc,seq[4]['vals'][0])=='onEnterFramexf'
    remove_ok=len(seq)>=6 and seq[5]['name']=='callpropvoid' and pname(abc,seq[5]['vals'][0])=='removeEventListener'
    checks.append(('minigame6 method length', len(body['code'])==1922))
    checks.append(('minigame6 skip branch', by.get(1853,{}).get('name')=='ifnlt' and by.get(1853,{}).get('targets')==[1918]))
    checks.append(('minigame6 cleanup sequence', seq_names==['getlocal0','getlex','getproperty','getlocal0','getproperty','callpropvoid'] and handler_ok and remove_ok))
    failed=[]
    for name,ok in checks:
        print(('PASS' if ok else 'FAIL')+': '+name)
        if not ok: failed.append(name)
    print(f'ABC classes={len(abc.classes)} method_bodies={len(abc.bodies)}')
    if len(abc.classes)!=462 or len(abc.bodies)!=3524: failed.append('ABC structure counts')
    if failed:
        print('FAILED: '+', '.join(failed),file=sys.stderr); return 1
    print('PASS: all four verified binary fixes are present'); return 0

if __name__=='__main__': raise SystemExit(main())
