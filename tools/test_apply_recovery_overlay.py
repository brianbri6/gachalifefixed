#!/usr/bin/env python3
from pathlib import Path
import tempfile
from apply_recovery_overlay import patch_one, RECOVERY_MARKER

def main():
    stub='''package x\n{\n   public class T\n   {\n      public function foo(evt:Object) : void\n      {\n         /* Decompilation error */\n         throw new flash.errors.IllegalOperationError("Not decompiled due to error");\n      }\n   }\n}\n'''
    generated='''public function foo(arg1:Object) : void\n{\n   var __pc:int = 0;\n   while(true)\n   {\n      return;\n   }\n}\n'''
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'foo.as'; p.write_text(generated)
        patched,status=patch_one(stub,'foo',p); assert status=='patched'; assert 'public function foo(evt:Object) : void' in patched; assert RECOVERY_MARKER in patched; assert 'IllegalOperationError' not in patched
        again,status2=patch_one(patched,'foo',p); assert status2=='already-recovered' and again==patched
        try: patch_one(stub.replace('Decompilation error','ordinary body').replace('throw new flash.errors.IllegalOperationError("Not decompiled due to error");','return;'),'foo',p)
        except ValueError: pass
        else: raise AssertionError('non-stub body must be refused')
    print('PASS: overlay replacement preserves signatures, rejects non-stubs, and is idempotent')
if __name__=='__main__': main()
