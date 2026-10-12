#!/usr/bin/env python3
from __future__ import annotations
import argparse, struct
from pathlib import Path
from abc_index import ABC, swf_abc

OPS={
0x01:('bkpt',()),0x02:('nop',()),0x03:('throw',()),0x04:('getsuper',('mn',)),0x05:('setsuper',('mn',)),0x06:('dxns',('str',)),0x07:('dxnslate',()),0x08:('kill',('u30',)),0x09:('label',()),
0x0c:('ifnlt',('s24',)),0x0d:('ifnle',('s24',)),0x0e:('ifngt',('s24',)),0x0f:('ifnge',('s24',)),0x10:('jump',('s24',)),0x11:('iftrue',('s24',)),0x12:('iffalse',('s24',)),0x13:('ifeq',('s24',)),0x14:('ifne',('s24',)),0x15:('iflt',('s24',)),0x16:('ifle',('s24',)),0x17:('ifgt',('s24',)),0x18:('ifge',('s24',)),0x19:('ifstricteq',('s24',)),0x1a:('ifstrictne',('s24',)),0x1b:('lookupswitch',('switch',)),0x1c:('pushwith',()),0x1d:('popscope',()),0x1e:('nextname',()),0x1f:('hasnext',()),
0x20:('pushnull',()),0x21:('pushundefined',()),0x23:('nextvalue',()),0x24:('pushbyte',('s8',)),0x25:('pushshort',('u30',)),0x26:('pushtrue',()),0x27:('pushfalse',()),0x28:('pushnan',()),0x29:('pop',()),0x2a:('dup',()),0x2b:('swap',()),0x2c:('pushstring',('str',)),0x2d:('pushint',('int',)),0x2e:('pushuint',('uint',)),0x2f:('pushdouble',('double',)),0x30:('pushscope',()),0x31:('pushnamespace',('ns',)),0x32:('hasnext2',('u30','u30')),
0x35:('li8',()),0x36:('li16',()),0x37:('li32',()),0x38:('lf32',()),0x39:('lf64',()),0x3a:('si8',()),0x3b:('si16',()),0x3c:('si32',()),0x3d:('sf32',()),0x3e:('sf64',()),
0x40:('newfunction',('method',)),0x41:('call',('u30',)),0x42:('construct',('u30',)),0x43:('callmethod',('u30','u30')),0x44:('callstatic',('method','u30')),0x45:('callsuper',('mn','u30')),0x46:('callproperty',('mn','u30')),0x47:('returnvoid',()),0x48:('returnvalue',()),0x49:('constructsuper',('u30',)),0x4a:('constructprop',('mn','u30')),0x4b:('callsuperid',('u30','u30')),0x4c:('callproplex',('mn','u30')),0x4d:('callinterface',('u30','u30')),0x4e:('callsupervoid',('mn','u30')),0x4f:('callpropvoid',('mn','u30')),
0x50:('sxi1',()),0x51:('sxi8',()),0x52:('sxi16',()),0x53:('applytype',('u30',)),
0x55:('newobject',('u30',)),0x56:('newarray',('u30',)),0x57:('newactivation',()),0x58:('newclass',('class',)),0x59:('getdescendants',('mn',)),0x5a:('newcatch',('u30',)),0x5b:('findpropglobalstrict',('mn',)),0x5c:('findpropglobal',('mn',)),0x5d:('findpropstrict',('mn',)),0x5e:('findproperty',('mn',)),0x5f:('finddef',('mn',)),0x60:('getlex',('mn',)),0x61:('setproperty',('mn',)),0x62:('getlocal',('u30',)),0x63:('setlocal',('u30',)),0x64:('getglobalscope',()),0x65:('getscopeobject',('u8',)),0x66:('getproperty',('mn',)),0x67:('getouterscope',('u30',)),0x68:('initproperty',('mn',)),0x69:('setpropertylate',()),0x6a:('deleteproperty',('mn',)),0x6b:('deletepropertylate',()),0x6c:('getslot',('u30',)),0x6d:('setslot',('u30',)),0x6e:('getglobalslot',('u30',)),0x6f:('setglobalslot',('u30',)),
0x70:('convert_s',()),0x71:('esc_xelem',()),0x72:('esc_xattr',()),0x73:('convert_i',()),0x74:('convert_u',()),0x75:('convert_d',()),0x76:('convert_b',()),0x77:('convert_o',()),0x78:('checkfilter',()),0x79:('convert_m',()),0x7a:('convert_m_p',('u30',)),0x7c:('convert_f',()),0x7d:('unplus',()),0x7e:('convert_f4',()),
0x80:('coerce',('mn',)),0x81:('coerce_b',()),0x82:('coerce_a',()),0x83:('coerce_i',()),0x84:('coerce_d',()),0x85:('coerce_s',()),0x86:('astype',('mn',)),0x87:('astypelate',()),0x88:('coerce_u',()),0x89:('coerce_o',()),
0x90:('negate',()),0x91:('increment',()),0x92:('inclocal',('u30',)),0x93:('decrement',()),0x94:('declocal',('u30',)),0x95:('typeof',()),0x96:('not',()),0x97:('bitnot',()),
0x9a:('concat',()),0x9b:('add_d',()),0x9c:('increment_p',('u30',)),0x9d:('inclocal_p',('u30','u30')),0x9e:('decrement_p',('u30',)),0x9f:('declocal_p',('u30','u30')),
0xa0:('add',()),0xa1:('subtract',()),0xa2:('multiply',()),0xa3:('divide',()),0xa4:('modulo',()),0xa5:('lshift',()),0xa6:('rshift',()),0xa7:('urshift',()),0xa8:('bitand',()),0xa9:('bitor',()),0xaa:('bitxor',()),0xab:('equals',()),0xac:('strictequals',()),0xad:('lessthan',()),0xae:('lessequals',()),0xaf:('greaterthan',()),0xb0:('greaterequals',()),0xb1:('instanceof',()),0xb2:('istype',('mn',)),0xb3:('istypelate',()),0xb4:('in',()),
0xb5:('add_p',('u30',)),0xb6:('subtract_p',('u30',)),0xb7:('multiply_p',('u30',)),0xb8:('divide_p',('u30',)),0xb9:('modulo_p',('u30',)),
0xc0:('increment_i',()),0xc1:('decrement_i',()),0xc2:('inclocal_i',('u30',)),0xc3:('declocal_i',('u30',)),0xc4:('negate_i',()),0xc5:('add_i',()),0xc6:('subtract_i',()),0xc7:('multiply_i',()),
0xd0:('getlocal0',()),0xd1:('getlocal1',()),0xd2:('getlocal2',()),0xd3:('getlocal3',()),0xd4:('setlocal0',()),0xd5:('setlocal1',()),0xd6:('setlocal2',()),0xd7:('setlocal3',()),
0xef:('debug',('debug',)),0xf0:('debugline',('u30',)),0xf1:('debugfile',('str',)),0xf2:('bkptline',('u30',)),0xf3:('timestamp',()),
}

def u30(code,p):
    v=0
    for i in range(5):
        b=code[p];p+=1;v|=(b&127)<<(7*i)
        if not b&128:return v,p
    return v&0x3fffffff,p

def s24(code,p):
    v=code[p]|(code[p+1]<<8)|(code[p+2]<<16);p+=3
    if v&0x800000:v-=1<<24
    return v,p

def fmt_operand(abc,typ,v):
    if typ=='mn': return f'{v}<{abc.mn(v)}>'
    if typ=='str': return f'{v}<{abc.s(v)!r}>'
    if typ=='int': return f'{v}<{abc.ints[v] if v<len(abc.ints) else "?"}>'
    if typ=='uint': return f'{v}<{abc.uints[v] if v<len(abc.uints) else "?"}>'
    if typ=='double': return f'{v}<{abc.doubles[v] if v<len(abc.doubles) else "?"}>'
    if typ=='ns': return f'{v}<{abc.ns(v)}>'
    if typ=='method':
        m=abc.methods[v] if v<len(abc.methods) else None
        return f'{v}<{abc.s(m["name_index"]) if m else "?"}>'
    return str(v)

def decode(abc,code):
    p=0; out=[]
    while p<len(code):
        start=p; op=code[p];p+=1
        if op not in OPS: raise ValueError(f'unknown opcode 0x{op:02x} at {start:#x}')
        name,types=OPS[op]; vals=[]; branch_targets=[]
        if types==('switch',):
            default,p=s24(code,p); count,p=u30(code,p); cases=[]
            for _ in range(count+1): x,p=s24(code,p); cases.append(x)
            vals=[default,count,*cases]; branch_targets=[start+default]+[start+x for x in cases]
        elif types==('debug',):
            vals.append(code[p]);p+=1; x,p=u30(code,p);vals.append(x); vals.append(code[p]);p+=1; x,p=u30(code,p);vals.append(x)
        else:
            for typ in types:
                if typ in ('u30','mn','str','int','uint','double','ns','method','class'): x,p=u30(code,p)
                elif typ=='s24': x,p=s24(code,p); branch_targets.append(p+x)
                elif typ=='u8': x=code[p];p+=1
                elif typ=='s8':
                    x=code[p];p+=1
                    if x>=128:x-=256
                else: raise ValueError(typ)
                vals.append(x)
        out.append({'offset':start,'op':op,'name':name,'types':types,'vals':vals,'end':p,'targets':branch_targets})
    return out

def find_method(abc,q):
    if q.isdigit(): return int(q)
    names=abc.method_name_map(); matches=[]
    for i,m in enumerate(abc.methods):
        hay=' '.join(names.get(i,[]))+' '+abc.s(m['name_index'])
        if q in hay: matches.append(i)
    if len(matches)!=1: raise SystemExit(f'method query {q!r} matched {matches}')
    return matches[0]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('swf',type=Path);ap.add_argument('method');ap.add_argument('--limit',type=int);args=ap.parse_args()
    abc=ABC(swf_abc(args.swf)); mid=find_method(abc,args.method); body=abc.bodies[mid]; ins=decode(abc,body['code'])
    aliases=abc.method_name_map().get(mid,[]);print(f'; method {mid}: {aliases} declared={abc.s(abc.methods[mid]["name_index"])!r} code={len(body["code"])} instructions={len(ins)}')
    n=args.limit or len(ins)
    for x in ins[:n]:
        if x['types']==('switch',):
            detail=f'default={x["targets"][0]:06x} cases={len(x["targets"])-1} '+','.join(f'{t:06x}' for t in x['targets'][1:8]) + ('...' if len(x['targets'])>8 else '')
        else:
            parts=[fmt_operand(abc,typ,v) for typ,v in zip(x['types'],x['vals'])]
            if x['targets']: parts.append('->'+','.join(f'{t:06x}' for t in x['targets']))
            detail=' '.join(parts)
        print(f'{x["offset"]:06x}: {x["name"]:<18} {detail}')
if __name__=='__main__':main()
