#!/usr/bin/env python3
"""Parse enough AVM2 ABC structure to index classes, methods, traits and raw method bodies."""
from __future__ import annotations
import argparse, json, struct, zlib
from dataclasses import dataclass
from pathlib import Path

class R:
    def __init__(self,b:bytes): self.b=b; self.p=0
    def u8(self): v=self.b[self.p]; self.p+=1; return v
    def u16(self): v=struct.unpack_from('<H',self.b,self.p)[0]; self.p+=2; return v
    def u30(self):
        result=0
        for i in range(5):
            x=self.u8(); result |= (x & 0x7f) << (7*i)
            if not (x & 0x80): return result & 0x3fffffff
        return result & 0x3fffffff
    def u32v(self):
        result=0
        for i in range(5):
            x=self.u8(); result |= (x & 0x7f) << (7*i)
            if not (x & 0x80): return result & 0xffffffff
        return result & 0xffffffff
    def s32(self):
        v=self.u32v(); return v-0x100000000 if v & 0x80000000 else v
    def bytes(self,n): v=self.b[self.p:self.p+n]; self.p+=n; return v
    def f64(self): v=struct.unpack_from('<d',self.b,self.p)[0]; self.p+=8; return v

def swf_abc(path:Path)->bytes:
    raw=path.read_bytes(); sig=raw[:3]
    if sig==b'CWS': data=raw[:8]+zlib.decompress(raw[8:])
    elif sig==b'FWS': data=raw
    else: raise ValueError(sig)
    p=8; nbits=data[p]>>3; p += (5+4*nbits+7)//8; p+=4
    while p+2<=len(data):
        rec=struct.unpack_from('<H',data,p)[0]; p+=2; code=rec>>6; ln=rec&63
        if ln==63: ln=struct.unpack_from('<I',data,p)[0]; p+=4
        body=data[p:p+ln]; p+=ln
        if code==82:
            nul=body.find(b'\0',4); return body[nul+1:]
    raise ValueError('no DoABC')

def parse_trait(r:R):
    name=r.u30(); ka=r.u8(); kind=ka&0x0f; attrs=ka>>4
    t={'name':name,'kind':kind,'attrs':attrs}
    if kind in (0,6):
        t['slot_id']=r.u30(); t['type_name']=r.u30(); t['vindex']=r.u30()
        if t['vindex']: t['vkind']=r.u8()
    elif kind in (1,2,3):
        t['disp_id']=r.u30(); t['method']=r.u30()
    elif kind==4:
        t['slot_id']=r.u30(); t['classi']=r.u30()
    elif kind==5:
        t['slot_id']=r.u30(); t['function']=r.u30()
    else: raise ValueError(f'bad trait kind {kind} at {r.p}')
    if attrs & 4:
        n=r.u30(); t['metadata']=[r.u30() for _ in range(n)]
    return t

def parse_traits(r:R): return [parse_trait(r) for _ in range(r.u30())]

class ABC:
    def __init__(self,b:bytes):
        self.r=R(b); r=self.r
        self.minor=r.u16(); self.major=r.u16()
        self.ints=[0]; n=r.u30(); self.ints += [r.s32() for _ in range(max(0,n-1))]
        self.uints=[0]; n=r.u30(); self.uints += [r.u32v() for _ in range(max(0,n-1))]
        self.doubles=[float('nan')]; n=r.u30(); self.doubles += [r.f64() for _ in range(max(0,n-1))]
        self.strings=['']; n=r.u30()
        for _ in range(max(0,n-1)):
            ln=r.u30(); self.strings.append(r.bytes(ln).decode('utf-8','replace'))
        self.namespaces=[None]; n=r.u30()
        for _ in range(max(0,n-1)): self.namespaces.append((r.u8(),r.u30()))
        self.nssets=[None]; n=r.u30()
        for _ in range(max(0,n-1)): self.nssets.append([r.u30() for __ in range(r.u30())])
        self.multinames=[None]; n=r.u30()
        for _ in range(max(0,n-1)):
            k=r.u8(); d={'kind':k}
            if k in (0x07,0x0d): d.update(ns=r.u30(),name=r.u30())
            elif k in (0x0f,0x10): d.update(name=r.u30())
            elif k in (0x11,0x12): pass
            elif k in (0x09,0x0e): d.update(name=r.u30(),nsset=r.u30())
            elif k in (0x1b,0x1c): d.update(nsset=r.u30())
            elif k==0x1d:
                d['qname']=r.u30(); d['params']=[r.u30() for __ in range(r.u30())]
            else: raise ValueError(f'bad multiname kind {k:#x} at {r.p}')
            self.multinames.append(d)
        self.methods=[]; n=r.u30()
        for i in range(n):
            pc=r.u30(); ret=r.u30(); pars=[r.u30() for _ in range(pc)]; name=r.u30(); flags=r.u8()
            m={'index':i,'param_types':pars,'return_type':ret,'name_index':name,'flags':flags}
            if flags & 0x08:
                oc=r.u30(); m['optional']=[(r.u30(),r.u8()) for _ in range(oc)]
            if flags & 0x80: m['param_names']=[r.u30() for _ in range(pc)]
            self.methods.append(m)
        self.metadata=[]; n=r.u30()
        for _ in range(n):
            name=r.u30(); cnt=r.u30(); keys=[r.u30() for __ in range(cnt)]; vals=[r.u30() for __ in range(cnt)]
            self.metadata.append((name,keys,vals))
        self.instances=[]; class_count=r.u30()
        for i in range(class_count):
            name=r.u30(); sup=r.u30(); flags=r.u8(); inst={'name':name,'super':sup,'flags':flags}
            if flags & 0x08: inst['protected_ns']=r.u30()
            inst['interfaces']=[r.u30() for _ in range(r.u30())]; inst['iinit']=r.u30(); inst['traits']=parse_traits(r); self.instances.append(inst)
        self.classes=[]
        for i in range(class_count): self.classes.append({'cinit':r.u30(),'traits':parse_traits(r)})
        self.scripts=[]; n=r.u30()
        for _ in range(n): self.scripts.append({'init':r.u30(),'traits':parse_traits(r)})
        self.bodies={}; n=r.u30()
        for _ in range(n):
            method=r.u30(); max_stack=r.u30(); local_count=r.u30(); init_scope=r.u30(); max_scope=r.u30()
            code_length_offset=r.p; clen=r.u30(); code_offset=r.p; code=r.bytes(clen)
            exc=[]
            for __ in range(r.u30()): exc.append(tuple(r.u30() for ___ in range(5)))
            traits=parse_traits(r)
            self.bodies[method]={'method':method,'max_stack':max_stack,'local_count':local_count,'init_scope_depth':init_scope,'max_scope_depth':max_scope,'code_length_offset':code_length_offset,'code_length_size':code_offset-code_length_offset,'code_offset':code_offset,'code':code,'exceptions':exc,'traits':traits}
    def s(self,i): return self.strings[i] if i and i<len(self.strings) else ''
    def ns(self,i):
        if not i or i>=len(self.namespaces) or self.namespaces[i] is None:return ''
        return self.s(self.namespaces[i][1])
    def mn(self,i):
        if not i or i>=len(self.multinames) or self.multinames[i] is None:return '*'
        d=self.multinames[i]; k=d['kind']
        if k in (0x07,0x0d):
            ns=self.ns(d['ns']); name=self.s(d['name']); return f'{ns}.{name}' if ns else name
        if k in (0x0f,0x10): return self.s(d['name'])
        if k in (0x09,0x0e): return self.s(d['name'])
        if k in (0x11,0x12,0x1b,0x1c): return '*'
        if k==0x1d:
            return self.mn(d['qname'])+'.<'+','.join(self.mn(x) for x in d['params'])+'>'
        return f'<mn {k:#x}>'
    def method_name_map(self):
        names={}
        kindname={1:'method',2:'get',3:'set'}
        for ci,inst in enumerate(self.instances):
            cn=self.mn(inst['name']); names.setdefault(inst['iinit'],[]).append(f'{cn}::<iinit>')
            for t in inst['traits']:
                if t['kind'] in kindname: names.setdefault(t['method'],[]).append(f'{cn}::{self.mn(t["name"])}')
            cl=self.classes[ci]; names.setdefault(cl['cinit'],[]).append(f'{cn}::<cinit>')
            for t in cl['traits']:
                if t['kind'] in kindname: names.setdefault(t['method'],[]).append(f'{cn}::{self.mn(t["name"])}')
        for si,sc in enumerate(self.scripts):
            names.setdefault(sc['init'],[]).append(f'<script{si}>::<init>')
            for t in sc['traits']:
                if t['kind'] in kindname: names.setdefault(t['method'],[]).append(f'<script{si}>::{self.mn(t["name"])}')
        return names

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('swf',type=Path); ap.add_argument('--class-name'); ap.add_argument('--json',type=Path); args=ap.parse_args()
    abc=ABC(swf_abc(args.swf)); names=abc.method_name_map(); out=[]
    for idx,m in enumerate(abc.methods):
        aliases=names.get(idx,[]); body=abc.bodies.get(idx)
        if args.class_name and not any(args.class_name in a for a in aliases): continue
        out.append({'index':idx,'aliases':aliases,'declared_name':abc.s(m['name_index']),'return_type':abc.mn(m['return_type']),'param_types':[abc.mn(x) for x in m['param_types']], 'code_length':len(body['code']) if body else None,'max_stack':body['max_stack'] if body else None,'locals':body['local_count'] if body else None})
    result={'abc_version':f'{abc.major}.{abc.minor}','methods':len(abc.methods),'classes':len(abc.instances),'bodies':len(abc.bodies),'matches':out}
    print(json.dumps(result,indent=2))
    if args.json: args.json.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__': main()
