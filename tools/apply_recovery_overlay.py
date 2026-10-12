#!/usr/bin/env python3
"""Apply validated binary-derived method bodies to a decompiled Gacha Life source tree.

The tool is deliberately conservative:
- it preserves the source method declaration/signature exactly;
- it replaces only method bodies that still contain a recognized decompiler-error stub;
- it refuses ambiguous/missing methods;
- --check performs a dry run;
- already recovered methods are skipped when they contain the recovery marker.
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUB_MARKERS = ('Not decompiled due', 'Decompilation error', 'IllegalOperationError')
RECOVERY_MARKER = '// RECOVERED_FROM_GACHALIFEPC_SWF'

def scan_matching_brace(text: str, open_pos: int) -> int:
    if open_pos >= len(text) or text[open_pos] != '{': raise ValueError('open_pos is not an opening brace')
    depth=0; i=open_pos; state='code'; quote=''
    while i < len(text):
        c=text[i]; n=text[i+1] if i+1<len(text) else ''
        if state=='code':
            if c in ('"', "'"): state,quote='string',c
            elif c=='/' and n=='/': state='line_comment'; i+=1
            elif c=='/' and n=='*': state='block_comment'; i+=1
            elif c=='{': depth+=1
            elif c=='}':
                depth-=1
                if depth==0:return i
        elif state=='string':
            if c=='\\': i+=1
            elif c==quote: state='code'
        elif state=='line_comment':
            if c in '\r\n': state='code'
        elif state=='block_comment' and c=='*' and n=='/': state='code'; i+=1
        i+=1
    raise ValueError('unbalanced method body')

def find_method_body(text:str,method:str)->tuple[int,int,int]:
    pat=re.compile(r'(?m)^[ \t]*(?:(?:public|private|protected|internal|static|final|override|native)\s+)*function\s+'+re.escape(method)+r'\s*\(')
    matches=list(pat.finditer(text))
    if len(matches)!=1: raise ValueError(f'expected exactly one declaration for {method!r}, found {len(matches)}')
    m=matches[0]; open_pos=text.find('{',m.end())
    if open_pos<0: raise ValueError(f'opening brace not found for {method!r}')
    return m.start(),open_pos,scan_matching_brace(text,open_pos)

def generated_inner_body(path:Path)->list[str]:
    text=path.read_text(encoding='utf-8'); open_pos=text.find('{')
    if open_pos<0: raise ValueError(f'no opening brace in generated method {path}')
    close_pos=scan_matching_brace(text,open_pos); inner=text[open_pos+1:close_pos].strip('\n'); lines=inner.splitlines()
    nonempty=[len(x)-len(x.lstrip(' ')) for x in lines if x.strip()]; common=min(nonempty) if nonempty else 0
    return [x[common:] if len(x)>=common else x for x in lines]

def patch_one(text:str,method:str,generated:Path,force:bool=False)->tuple[str,str]:
    _,open_pos,close_pos=find_method_body(text,method); existing=text[open_pos+1:close_pos]
    if RECOVERY_MARKER in existing:return text,'already-recovered'
    if not force and not any(marker in existing for marker in STUB_MARKERS): raise ValueError(f'{method}: target body is not a recognized decompiler-error stub; refusing replacement')
    line_start=text.rfind('\n',0,open_pos)+1; signature_indent=re.match(r'[ \t]*',text[line_start:open_pos]).group(0); body_indent=signature_indent+'   '
    body_lines=[RECOVERY_MARKER]+generated_inner_body(generated)
    replacement='\n'+'\n'.join(body_indent+ln if ln else '' for ln in body_lines)+'\n'+signature_indent
    return text[:open_pos+1]+replacement+text[close_pos:],'patched'

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('source_root',type=Path,help='root of the decompiled source checkout'); ap.add_argument('--manifest',type=Path,default=ROOT/'recovery_manifest.json'); ap.add_argument('--check',action='store_true',help='validate patchability without writing files'); ap.add_argument('--force',action='store_true',help='replace non-stub target methods (unsafe; normally do not use)'); args=ap.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding='utf-8')); grouped={}
    for rec in manifest['recoveries']: grouped.setdefault(rec['source_file'],[]).append(rec)
    changed_files=patched_methods=already=0; errors=[]
    for rel,recs in grouped.items():
        path=args.source_root/rel
        if not path.exists(): errors.append(f'{rel}: source file missing'); continue
        try:
            original=path.read_text(encoding='utf-8'); updated=original; local_patched=0
            for rec in recs:
                generated=ROOT/rec['generated_body']
                if not generated.exists(): raise ValueError(f"{rec['method']}: missing generated body {rec['generated_body']}")
                updated,status=patch_one(updated,rec['method'],generated,force=args.force)
                if status=='patched': local_patched+=1; patched_methods+=1
                else: already+=1
            if updated!=original:
                changed_files+=1
                if not args.check:path.write_text(updated,encoding='utf-8')
            print(f'{rel}: {local_patched} method(s) patchable'+(' [check only]' if args.check else ''))
        except Exception as e: errors.append(f'{rel}: {e}')
    print(f'summary: files_changed={changed_files}, methods_patched={patched_methods}, already_recovered={already}')
    if errors:
        print(f'FAILED with {len(errors)} issue(s):',file=sys.stderr)
        for e in errors: print(f' - {e}',file=sys.stderr)
        return 1
    return 0
if __name__=='__main__': raise SystemExit(main())
