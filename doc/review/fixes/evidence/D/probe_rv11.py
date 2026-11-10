"""Capture successful failure-tool launch and compiler diagnostics with a spaced Python."""
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
records = []


def run(*command):
    command = [str(a) for a in command]
    result = subprocess.run(command, cwd=ROOT, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'),
                            capture_output=True, text=True, timeout=30)
    records.append(dict(command=command, exit_code=result.returncode, stdout=result.stdout, stderr=result.stderr))
    return result


with tempfile.TemporaryDirectory(prefix="minic Python's path ") as directory:
    root = Path(directory)
    interpreter = root / 'python3.11'
    interpreter.symlink_to(sys.executable)
    tool = root / 'failing-clang'
    payload = 'import sys; print("test clang diagnostic", file=sys.stderr); sys.exit(7)'
    tool.write_text(f'#!/bin/sh\nexec {shlex.quote(str(interpreter))} -c {shlex.quote(payload)}\n')
    tool.chmod(0o755)
    direct = run(tool)
    assert (direct.returncode,direct.stdout,direct.stderr)==(7,'','test clang diagnostic\n')
    frontend=root/'frontend'
    assert run(interpreter,'-B','-m','ccgen','--lex','rules/minic.lex','--grammar','rules/minic.grammar','--out',frontend).returncode==0
    out=root/'compiled'
    result=run(interpreter,'-B','-m','minic','examples/demo.mc','--frontend',frontend,'--out',out,'--clang',tool)
    assert (result.returncode,result.stdout,result.stderr)==(3,'','后端错误: test clang diagnostic\nclang 执行失败，退出码 7\n')
    products=sorted(p.name for p in out.iterdir())
    assert set(products)=={'tokens.txt','tokens.json','ast.json','ast.txt','ast.html','ast.dot','demo.ll'}
    (HERE/'rv11-tool-proof.json').write_text(json.dumps({'records':records,'products':products},ensure_ascii=False,indent=2)+'\n')
print('tool exit 7, exact diagnostic; compiler exit 3; all seven frontend/IR artifacts preserved')
