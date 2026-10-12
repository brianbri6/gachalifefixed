#!/usr/bin/env python3
from pathlib import Path

TARGET = Path('binary_reconstructed_source/GachaLifePC_fla/MainTimeline.as')

FIXES = [
    (
        'random-string final character reachable',
        '                  _loc3_ = Number((((_loc2_)["length"]) - 1));',
        '                  _loc3_ = Number((_loc2_)["length"]);',
    ),
    (
        'minigame2 remove movement listener from same dispatcher',
        '                  (stage)["removeEventListener"]((Event)["ENTER_FRAME"], (this)["onEnterFramex"]);',
        '                  removeEventListener((Event)["ENTER_FRAME"], (this)["onEnterFramex"]);',
    ),
    (
        'minigame6 remove movement listener on game over',
        '                  (stage)["removeEventListener"]((Event)["ENTER_FRAME"], (this)["minigameloop6"]);\n                  __pc = 1902;',
        '                  (stage)["removeEventListener"]((Event)["ENTER_FRAME"], (this)["minigameloop6"]);\n                  removeEventListener((Event)["ENTER_FRAME"], (this)["onEnterFramexf"]);\n                  __pc = 1902;',
    ),
]

def apply_fixes(target: Path = TARGET):
    text = target.read_text(encoding='utf-8')
    changed = []
    for name, old, new in FIXES:
        count = text.count(old)
        if count == 0: continue
        if count != 1: raise SystemExit(f'{name}: expected exactly one match, got {count}')
        text = text.replace(old, new, 1); changed.append(name)
    zero_guard = '      public function addComma(gotoAndStop:uint) : String\n      {\n'
    guard_body = zero_guard + '         if(gotoAndStop == 0)\n         {\n            return "0";\n         }\n'
    if guard_body not in text:
        count = text.count(zero_guard)
        if count != 1: raise SystemExit(f'addComma zero guard: expected exactly one match, got {count}')
        text = text.replace(zero_guard, guard_body, 1); changed.append('addComma zero guard')
    target.write_text(text, encoding='utf-8'); return changed

def main():
    changed = apply_fixes(); print('applied:', ', '.join(changed) if changed else 'already up to date')
if __name__ == '__main__': main()
