#!/usr/bin/env python3
"""Generate a code-only ActionScript source tree from GachaLifePC.swf ABC."""
from __future__ import annotations
import argparse,json,re,shutil,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent; sys.path.insert(0,str(HERE))
from abc_index import ABC,swf_abc
from avm2_to_as3_state import emit_method,prop_name,const_value,safe_ident
from apply_safe_binary_source_fixes import apply_fixes
NS_PRIVATE=0x05; NS_PACKAGE=0x16; NS_INTERNAL=0x17; NS_PROTECTED=0x18; NS_STATIC_PROTECTED=0x1A
OVERRIDES={9:ROOT/'manual_overrides/9_setTextField.as',19:ROOT/'manual_overrides/19_fromXML.as',31:ROOT/'manual_overrides/31_parseXML.as',432:ROOT/'manual_overrides/432_depthgo.as'}

def split_qname(q:str)->tuple[str,str]: return q.rsplit('.',1) if '.' in q else ('',q)
def simple_type(t:str)->str: return '*' if t=='*' else t.replace('__AS3__.vec.Vector','Vector')
def trait_parts(abc:ABC,t:dict)->tuple[str,str,int]:
    d=abc.multinames[t['name']]; name=prop_name(abc,t['name']) or abc.mn(t['name']).split('.')[-1]; nsidx=d.get('ns',0) if d else 0; kind=abc.namespaces[nsidx][0] if nsidx and abc.namespaces[nsidx] else NS_PACKAGE
    vis='private' if kind==NS_PRIVATE else 'protected' if kind in (NS_PROTECTED,NS_STATIC_PROTECTED) else 'internal' if kind==NS_INTERNAL else 'public'
    return safe_ident(name,'member'),vis,kind

def member_mods(vis:str,t:dict,is_static:bool)->str:
    mods=[]
    if not is_static and t.get('attrs',0)&2:mods.append('override')
    mods.append(vis)
    if is_static:mods.append('static')
    if not is_static and t.get('attrs',0)&1:mods.append('final')
    return ' '.join(mods)

def constructor_source(abc:ABC,mid:int,class_name:str)->str:
    text=emit_method(abc,mid,method_name=class_name,visibility='public'); lines=text.splitlines(); lines[0]=re.sub(r'\s*:\s*[^\s{]+\s*$','',lines[0]); super_i=next((i for i,l in enumerate(lines) if l.strip().startswith('super(')),None)
    if super_i is None:raise ValueError(f'constructor {class_name} method {mid}: super() not found')
    super_line=lines.pop(super_i).strip(); lines.insert(2,'   '+super_line); return '\n'.join(lines)+'\n'

def emit_trait_method(abc:ABC,t:dict,is_static:bool,class_name:str)->str:
    mid=t['method']
    if mid in OVERRIDES:return OVERRIDES[mid].read_text(encoding='utf-8')
    name,vis,_=trait_parts(abc,t); method_name=('get '+name if t['kind']==2 else 'set '+name if t['kind']==3 else name)
    return emit_method(abc,mid,method_name=method_name,visibility=member_mods(vis,t,is_static),local0_expr=(class_name if is_static else 'this'))

def emit_slot(abc:ABC,t:dict,is_static:bool)->str:
    name,vis,_=trait_parts(abc,t); typ=simple_type(abc.mn(t.get('type_name',0))); kind='const' if t['kind']==6 else 'var'; mods=f'{vis}'+(' static' if is_static else ''); init=''
    if t.get('vindex',0):init=' = '+const_value(abc,t['vindex'],t['vkind'])
    return f'{mods} {kind} {name}:{typ}{init};'
def indent(text:str,n:int=6)->str:
    pad=' '*n; return '\n'.join((pad+l if l else '') for l in text.rstrip().splitlines())

def class_source(abc:ABC,ci:int,imports:list[str])->str:
    inst=abc.instances[ci]; cl=abc.classes[ci]; qn=abc.mn(inst['name']); pkg,name=split_qname(qn); sup=simple_type(abc.mn(inst['super'])); flags=inst['flags']; mods=['public']
    if flags&0x02:mods.append('final')
    if not(flags&0x01):mods.append('dynamic')
    kind='interface' if flags&0x04 else 'class'; head=' '.join(mods+[kind,name])
    if kind=='class' and sup not in ('','*','Object'):head+=' extends '+sup
    if inst.get('interfaces'):head+=(' extends ' if kind=='interface' else ' implements ')+', '.join(simple_type(abc.mn(x)) for x in inst['interfaces'])
    out=[f'package {pkg}' if pkg else 'package','{']
    for imp in imports:
        if imp and imp!=pkg:out.append(f'   import {imp}.*;')
    out+=['',f'   {head}','   {']
    for t in inst['traits']:
        if t['kind'] in (0,6):out.append('      '+emit_slot(abc,t,False))
    if any(t['kind'] in (0,6) for t in inst['traits']):out.append('')
    for t in cl['traits']:
        if t['kind'] in (0,6):out.append('      '+emit_slot(abc,t,True))
    if any(t['kind'] in (0,6) for t in cl['traits']):out.append('')
    if kind=='class':out.append(indent(constructor_source(abc,inst['iinit'],name),6));out.append('')
    for t in inst['traits']:
        if t['kind'] in (1,2,3):out.append(indent(emit_trait_method(abc,t,False,name),6));out.append('')
    for t in cl['traits']:
        if t['kind'] in (1,2,3):out.append(indent(emit_trait_method(abc,t,True,name),6));out.append('')
    while out and out[-1]=='':out.pop()
    out+=['   }','}',''];return '\n'.join(out)

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('swf',type=Path,nargs='?',default=Path('/mnt/data/gacha-recovery/GachaLifePC.swf'));ap.add_argument('-o','--output',type=Path,default=ROOT/'binary_reconstructed_source');ap.add_argument('--clean',action='store_true');args=ap.parse_args()
    if args.clean and args.output.exists():shutil.rmtree(args.output)
    args.output.mkdir(parents=True,exist_ok=True);abc=ABC(swf_abc(args.swf));imports=sorted({abc.ns(i) for i,n in enumerate(abc.namespaces) if i and n and n[0]==NS_PACKAGE and abc.ns(i) and abc.ns(i)!='__AS3__.vec'});generated=[];failures=[]
    for ci,inst in enumerate(abc.instances):
        qn=abc.mn(inst['name']);pkg,name=split_qname(qn);rel=(Path(*pkg.split('.')) if pkg else Path())/(name+'.as');path=args.output/rel;path.parent.mkdir(parents=True,exist_ok=True)
        try:
            text=class_source(abc,ci,imports);path.write_text(text,encoding='utf-8');generated.append({'class_index':ci,'class':qn,'file':str(rel),'bytes':len(text.encode('utf-8'))})
        except Exception as e:failures.append({'class_index':ci,'class':qn,'error':str(e)})
    report={'classes_total':len(abc.instances),'classes_generated':len(generated),'failures':failures,'manual_method_overrides':{str(k):str(v.relative_to(ROOT)) for k,v in OVERRIDES.items()},'generated':generated};(args.output/'RECONSTRUCTION_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    if not failures:apply_fixes(args.output/'GachaLifePC_fla/MainTimeline.as')
    (args.output/'README.md').write_text('# Binary-reconstructed ActionScript code tree\n\nGenerated from the user-provided `GachaLifePC.swf` ABC bytecode. This tree reconstructs ActionScript class/member code only. It does **not** recreate Adobe Animate timeline graphics, library symbols, embedded bitmap/audio assets, or original FLA/XFL authoring metadata.\n\nMost methods are correctness-first state-machine translations. See `../recovery_manifest.json` for the higher-confidence source-pack stub recoveries and `../manual_overrides/` for the high-level semantic overrides.\n',encoding='utf-8')
    print(f'generated {len(generated)}/{len(abc.instances)} classes into {args.output}')
    if failures:
        for f in failures:print(f"FAIL {f['class']}: {f['error']}",file=sys.stderr)
        return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
