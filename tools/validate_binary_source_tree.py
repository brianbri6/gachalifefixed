#!/usr/bin/env python3
"""Static validation for the binary-reconstructed AS3 code tree."""
from __future__ import annotations
import argparse,json,re,sys
from pathlib import Path
STUBS=('Not decompiled due','Decompilation error','IllegalOperationError("Not decompiled')
RESERVED=set("as break case catch class const continue default delete do else extends false finally for function get if implements import in include instanceof interface internal is namespace native new null package private protected public return set static super switch this throw true try typeof use var void while with each final dynamic override".split())

def mask_noncode(text:str)->str:
    out=list(text);i=0;state='code';quote=''
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if state=='code':
            if c=='/' and n=='/':out[i]=out[i+1]=' ';i+=2;state='line';continue
            if c=='/' and n=='*':out[i]=out[i+1]=' ';i+=2;state='block';continue
            if c in ('"',"'"):quote=c;out[i]=' ';i+=1;state='string';continue
            i+=1
        elif state=='line':
            if c in '\r\n':state='code'
            else:out[i]=' '
            i+=1
        elif state=='block':
            if c=='*' and n=='/':out[i]=out[i+1]=' ';i+=2;state='code'
            else:out[i]=' ';i+=1
        else:
            if c=='\\':
                out[i]=' ';i+=1
                if i<len(text):out[i]=' ';i+=1
            elif c==quote:out[i]=' ';i+=1;state='code'
            else:out[i]=' ';i+=1
    return ''.join(out)

def function_spans(text:str):
    masked=mask_noncode(text);spans=[]
    for m in re.finditer(r'\bfunction\b[^\{;]*\{',masked):
        brace=m.end()-1;depth=1;i=brace+1
        while i<len(masked) and depth:
            if masked[i]=='{':depth+=1
            elif masked[i]=='}':depth-=1
            i+=1
        if depth==0:spans.append((m.start(),i))
    return spans

def braces_ok(text:str)->bool:
    depth=0;i=0;state='code';quote=''
    while i<len(text):
        c=text[i];n=text[i+1] if i+1<len(text) else ''
        if state=='code':
            if c in ('"',"'"):state='string';quote=c
            elif c=='/' and n=='/':state='line';i+=1
            elif c=='/' and n=='*':state='block';i+=1
            elif c=='{':depth+=1
            elif c=='}':
                depth-=1
                if depth<0:return False
        elif state=='string':
            if c=='\\':i+=1
            elif c==quote:state='code'
        elif state=='line':
            if c in '\r\n':state='code'
        elif state=='block' and c=='*' and n=='/':state='code';i+=1
        i+=1
    return depth==0 and state not in ('string','block')

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument('tree',type=Path,nargs='?',default=Path(__file__).resolve().parent.parent/'binary_reconstructed_source');args=ap.parse_args();report_path=args.tree/'RECONSTRUCTION_REPORT.json';errors=[]
    if not report_path.exists():print('missing RECONSTRUCTION_REPORT.json',file=sys.stderr);return 1
    report=json.loads(report_path.read_text())
    if report['classes_generated']!=report['classes_total'] or report['failures']:errors.append(f"report incomplete: {report['classes_generated']}/{report['classes_total']} classes, failures={len(report['failures'])}")
    files=sorted(args.tree.rglob('*.as'))
    if len(files)!=report['classes_generated']:errors.append(f'AS file count {len(files)} != report class count {report["classes_generated"]}')
    total=0
    for p in files:
        s=p.read_text(encoding='utf-8');total+=len(s.encode('utf-8'))
        if not braces_ok(s):errors.append(f'{p}: lexical brace/string/comment balance failed')
        for marker in STUBS:
            if marker in s:errors.append(f'{p}: contains decompiler stub marker {marker!r}')
        if 'public static final function' in s or 'public static override function' in s:errors.append(f'{p}: invalid/redundant static method modifier combination')
        for fm in re.finditer(r'\bfunction\s+[A-Za-z_$][\w$]*\s*\(([^)]*)\)',s):
            raw=fm.group(1).strip()
            if not raw:continue
            names=[]
            for part in raw.split(','):
                m=re.match(r'\s*([A-Za-z_$][\w$]*)\s*:',part)
                if m:names.append(m.group(1))
            if len(names)!=len(set(names)):errors.append(f'{p}: duplicate parameter name in {fm.group(0)[:120]}');break
        for m in re.finditer(r'\(([A-Za-z_$][\w$]*)\)\["\1"\]\s*=',s):errors.append(f'{p}: suspicious self-property assignment from scope emission: {m.group(0)}');break
        spill_pairs=set(re.findall(r'\b(__stk\d+)\s*=\s*([A-Za-z_$][\w$]*)\s*;',s))
        for spill,name in spill_pairs:
            if f'({spill})["{name}"] =' in s:errors.append(f'{p}: unresolved scope spill assignment for {name} via {spill}');break
        if not re.search(r'(?m)^package(?:\s+[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*)?\s*$',s):errors.append(f'{p}: package declaration not found')
        decl=re.search(r'\b(?:class|interface)\s+([A-Za-z_$][\w$]*)',s)
        if not decl:errors.append(f'{p}: class/interface declaration not found')
        else:
            pm=re.search(r'(?m)^package(?:\s+([A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*))?\s*$',s);package=pm.group(1) if pm and pm.group(1) else '';expected=Path(*(package.split('.') if package else []))/(decl.group(1)+'.as')
            if p.relative_to(args.tree)!=expected:errors.append(f'{p}: source path does not match declared QName; expected {expected}')
        if 'new (' in s:errors.append(f'{p}: parenthesized constructor expression remains (likely invalid AS3)')
        for fm in re.finditer(r'\bfunction\s+([A-Za-z_$][\w$]*)\s*\(([^)]*)\)',s):
            if fm.group(1) in RESERVED:errors.append(f'{p}: reserved word used as function identifier: {fm.group(1)}');break
            for q in re.finditer(r'(?:^|,)\s*([A-Za-z_$][\w$]*)\s*:',fm.group(2)):
                if q.group(1) in RESERVED:errors.append(f'{p}: reserved word used as parameter identifier: {q.group(1)}');break
        spans=function_spans(s)
        for st,en in spans:
            chunk=s[st:en]
            if 'switch(__pc)' not in chunk:continue
            arr=list(chunk)
            for nst,nen in spans:
                if st<nst and nen<=en:
                    for k in range(nst-st,nen-st):arr[k]=' '
            chunk=''.join(arr);cases=[int(x) for x in re.findall(r'\bcase\s+(-?\d+)\s*:',chunk)]
            if len(cases)!=len(set(cases)):errors.append(f'{p}: duplicate __pc case label in generated state machine');break
            targets=[int(x) for x in re.findall(r'__pc\s*=\s*(-?\d+)\s*;',chunk)]
            for a,b in re.findall(r'__pc\s*=\s*\([^;?]+\)\s*\?\s*(-?\d+)\s*:\s*(-?\d+)\s*;',chunk):targets.extend((int(a),int(b)))
            missing=sorted(set(targets)-set(cases))
            if missing:errors.append(f'{p}: __pc transition(s) target missing case labels: {missing[:12]}');break
    probes={'p.as':'with(clickSprite.graphics)','fl/motion/Color.as':'for each(_loc3_ in _loc2_.attributes())','GachaLifePC_fla/MainTimeline.as':'for(i in someArray)'}
    main_text=(args.tree/'GachaLifePC_fla/MainTimeline.as').read_text(encoding='utf-8') if (args.tree/'GachaLifePC_fla/MainTimeline.as').exists() else ''
    fix_probes={'random-string uses full character set':'_loc3_ = Number((_loc2_)["length"]);','addComma zero guard':'if(gotoAndStop == 0)','minigame2 same-dispatcher cleanup':'(stage)["removeEventListener"]((Event)["ENTER_FRAME"], (this)["minigameloop2"]);\n                  removeEventListener((Event)["ENTER_FRAME"], (this)["onEnterFramex"]);','minigame6 movement cleanup':'(stage)["removeEventListener"]((Event)["ENTER_FRAME"], (this)["minigameloop6"]);\n                  removeEventListener((Event)["ENTER_FRAME"], (this)["onEnterFramexf"]);'}
    for label,probe in fix_probes.items():
        if probe not in main_text:errors.append(f'MainTimeline.as: safe-fix probe missing: {label}')
    for rel,needle in probes.items():
        p=args.tree/rel
        if not p.exists() or needle not in p.read_text(encoding='utf-8'):errors.append(f'{rel}: semantic override probe missing: {needle}')
    print(f'classes={len(files)} bytes={total} report_failures={len(report["failures"])}')
    if errors:
        print(f'FAILED with {len(errors)} issue(s):',file=sys.stderr)
        for e in errors[:100]:print(' - '+e,file=sys.stderr)
        return 1
    print('PASS: reconstructed class tree is complete by report, stub-free, and statically balanced');return 0
if __name__=='__main__':raise SystemExit(main())
