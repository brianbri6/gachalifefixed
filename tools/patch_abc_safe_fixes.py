#!/usr/bin/env python3
"""Apply SWF-verified gameplay fixes directly to an AVM2 ABC payload.

Three fixes preserve method length. The minigame-6 cleanup inserts one call at the
end of its game-over branch and adjusts the single branch that jumps across that
insertion. The method-body code-length U30 is updated; all other ABC tables stay
byte-for-byte intact.
"""
from __future__ import annotations
import argparse, json, struct, sys, zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from abc_index import ABC
from avm2_disasm import decode

NOP=0x02
GETLOCAL0=0xD0
PUSHBYTE=0x24
CONVERT_S=0x70
RETURNVALUE=0x48
IFNE=0x14

def u30(v:int)->bytes:
    if v < 0 or v > 0x3fffffff: raise ValueError(v)
    out=bytearray()
    while True:
        b=v & 0x7f; v >>= 7
        if v: out.append(b|0x80)
        else:
            out.append(b); return bytes(out)

def s24(v:int)->bytes:
    if not -(1<<23) <= v < (1<<23): raise ValueError(v)
    return int(v & 0xffffff).to_bytes(3,'little')

def pname(abc,mi):
    d=abc.multinames[mi]
    return abc.s(d.get('name',0)) if d else ''

def method_id(abc,suffix,owner=None):
    hits=[]
    for mid,names in abc.method_name_map().items():
        for n in names:
            if n.endswith('::'+suffix) and (owner is None or n.startswith(owner+'::')):
                hits.append(mid); break
    if len(hits)!=1: raise RuntimeError(f'{owner or "*"}::{suffix}: expected one method, got {hits}')
    return hits[0]

def mn_index(abc,name:str)->int:
    hits=[i for i,d in enumerate(abc.multinames) if d and abc.s(d.get('name',0))==name]
    pub=[i for i in hits if abc.multinames[i].get('kind') in (0x09,0x0e) and abc.multinames[i].get('nsset')==15]
    if len(pub)==1: return pub[0]
    if len(hits)==1: return hits[0]
    raise RuntimeError(f'multiname {name!r}: ambiguous indexes {hits}')

def patch_instruction(buf:bytearray, body, ins, replacement:bytes, label:str):
    n=ins['end']-ins['offset']
    if len(replacement)!=n: raise RuntimeError(f'{label}: replacement len {len(replacement)} != instruction len {n}')
    off=body['code_offset']+ins['offset']
    before=bytes(buf[off:off+n]); buf[off:off+n]=replacement
    return {'label':label,'abc_offset':off,'method_offset':ins['offset'],'before':before.hex(),'after':replacement.hex(),'length_delta':0}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('input',type=Path,nargs='?',default=Path(__file__).resolve().parent.parent/'swf_shell/original.abc.z')
    ap.add_argument('-o','--output',type=Path,default=Path(__file__).resolve().parent.parent/'build/patched-safe.abc')
    ap.add_argument('--input-zlib',action='store_true',default=None)
    a=ap.parse_args()
    raw=a.input.read_bytes()
    compressed = a.input.suffix=='.z' if a.input_zlib is None else a.input_zlib
    abc_bytes=zlib.decompress(raw) if compressed else raw
    abc=ABC(abc_bytes); buf=bytearray(abc_bytes); patches=[]
    owner='GachaLifePC_fla.MainTimeline'

    mid=method_id(abc,'generateRandomString',owner); body=abc.bodies[mid]; ins=decode(abc,body['code'])
    cand=[]
    for i,x in enumerate(ins):
        if x['name']=='decrement' and i>=1 and ins[i-1]['name']=='getproperty' and pname(abc,ins[i-1]['vals'][0])=='length': cand.append(x)
    if len(cand)!=1: raise RuntimeError(f'generateRandomString decrement candidates={len(cand)}')
    patches.append(patch_instruction(buf,body,cand[0],bytes([NOP]),'generateRandomString full character range'))

    mid=method_id(abc,'minigameloop2',owner); body=abc.bodies[mid]; ins=decode(abc,body['code'])
    target=None
    for i,x in enumerate(ins):
        if x['name']!='getlex' or pname(abc,x['vals'][0])!='stage': continue
        window=ins[i:i+8]
        if any(y['name']=='getproperty' and y['vals'] and pname(abc,y['vals'][0])=='onEnterFramex' for y in window):
            target=x; break
    if target is None: raise RuntimeError('minigame2 stage receiver for onEnterFramex cleanup not found')
    n=target['end']-target['offset']
    patches.append(patch_instruction(buf,body,target,bytes([GETLOCAL0])+bytes([NOP])*(n-1),'minigame2 same-dispatcher cleanup'))

    mid=method_id(abc,'addComma',owner); body=abc.bodies[mid]; code=body['code']; ins=decode(abc,code)
    byoff={x['offset']:x for x in ins}
    if byoff.get(12,{}).get('name')!='debug' or byoff.get(19,{}).get('name')!='debug' or byoff.get(26,{}).get('name')!='pushstring':
        raise RuntimeError('addComma prologue shape changed; refusing unsafe patch')
    repl=bytes([0xD1,PUSHBYTE,0,IFNE])+s24(7)+bytes([PUSHBYTE,0,CONVERT_S,RETURNVALUE,NOP,NOP,NOP])
    if len(repl)!=14: raise AssertionError(len(repl))
    off=body['code_offset']+12; before=bytes(buf[off:off+14]); buf[off:off+14]=repl
    patches.append({'label':'addComma zero formatting','abc_offset':off,'method_offset':12,'before':before.hex(),'after':repl.hex(),'length_delta':0})

    mid=method_id(abc,'minigameloop6',owner); body=abc.bodies[mid]; ins=decode(abc,body['code']); byoff={x['offset']:x for x in ins}
    branch=byoff.get(1853); existing_call=byoff.get(1898); ret=byoff.get(1905)
    if not branch or branch['name']!='ifnlt' or branch['vals']!=[45]: raise RuntimeError('minigame6 branch shape changed')
    if not existing_call or existing_call['name']!='callpropvoid' or pname(abc,existing_call['vals'][0])!='removeEventListener': raise RuntimeError('minigame6 cleanup call shape changed')
    if not ret or ret['name']!='returnvoid': raise RuntimeError('minigame6 return shape changed')
    event_mn=mn_index(abc,'Event'); enter_mn=mn_index(abc,'ENTER_FRAME'); handler_mn=mn_index(abc,'onEnterFramexf'); remove_mn=mn_index(abc,'removeEventListener')
    insert=(bytes([GETLOCAL0])+bytes([0x60])+u30(event_mn)+bytes([0x66])+u30(enter_mn)+bytes([GETLOCAL0])+bytes([0x66])+u30(handler_mn)+bytes([0x4f])+u30(remove_mn)+u30(2))
    if len(insert)!=16: raise RuntimeError(f'unexpected minigame6 cleanup encoding length {len(insert)}')
    branch_abs=body['code_offset']+branch['offset']
    old_branch=bytes(buf[branch_abs:branch_abs+4]); new_branch=bytes([0x0c])+s24(45+len(insert)); buf[branch_abs:branch_abs+4]=new_branch
    patches.append({'label':'minigame6 skip-branch adjustment','abc_offset':branch_abs,'method_offset':branch['offset'],'before':old_branch.hex(),'after':new_branch.hex(),'length_delta':0})
    insert_at_method=existing_call['end']; insert_abs=body['code_offset']+insert_at_method; buf[insert_abs:insert_abs]=insert
    old_len=len(body['code']); new_len=old_len+len(insert); old_enc=u30(old_len); new_enc=u30(new_len)
    if len(old_enc)!=body['code_length_size'] or len(new_enc)!=body['code_length_size']: raise RuntimeError('minigame6 code_length U30 width changed; targeted writer refuses')
    clo=body['code_length_offset']; before_len=bytes(buf[clo:clo+body['code_length_size']]); buf[clo:clo+body['code_length_size']]=new_enc
    patches.append({'label':'minigame6 onEnterFramexf cleanup insertion','abc_offset':insert_abs,'method_offset':insert_at_method,'before':'','after':insert.hex(),'length_delta':len(insert),'code_length_before':old_len,'code_length_after':new_len,'code_length_bytes_before':before_len.hex(),'code_length_bytes_after':new_enc.hex()})

    outabc=ABC(bytes(buf))
    if len(outabc.classes)!=len(abc.classes) or len(outabc.bodies)!=len(abc.bodies): raise RuntimeError('ABC structure count changed unexpectedly')
    add_body=outabc.bodies[method_id(outabc,'addComma',owner)]; add_ins=decode(outabc,add_body['code'])
    if not (any(x['name']=='getlocal1' and x['offset']==12 for x in add_ins) and any(x['name']=='returnvalue' and x['offset']==22 for x in add_ins) and any(x['name']=='ifne' and x.get('targets')==[26] for x in add_ins)):
        raise RuntimeError('addComma zero guard verification failed')
    mini_body=outabc.bodies[method_id(outabc,'minigameloop6',owner)]; mini_ins=decode(outabc,mini_body['code'])
    cleanups=[]
    for i,x in enumerate(mini_ins):
        if x['name']=='getproperty' and x['vals'] and pname(outabc,x['vals'][0]) in ('minigameloop6','onEnterFramexf'):
            cleanups.append((pname(outabc,x['vals'][0]), x['offset']))
    if not any(n=='onEnterFramexf' and off>1900 for n,off in cleanups): raise RuntimeError('minigame6 inserted cleanup verification failed')

    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_bytes(buf)
    report=a.output.with_suffix(a.output.suffix+'.json'); report.write_text(json.dumps({'input':str(a.input),'output':str(a.output),'abc_length_before':len(abc_bytes),'abc_length_after':len(buf),'patches':patches},indent=2)+'\n')
    print(json.dumps({'abc_length_before':len(abc_bytes),'abc_length_after':len(buf),'patches':patches},indent=2))

if __name__=='__main__': main()
