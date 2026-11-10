"""clang handles optimization, assembly and linking; no third-party libraries."""
import os
from pathlib import Path
import subprocess


class BackendError(Exception):
    pass


def build(ir, optimization=2, clang='clang'):
    ir = Path(ir).resolve()
    # Relative explicit tool paths are relative to the caller, not the output dir.
    if os.path.dirname(clang):
        clang = str(Path(clang).resolve())
    executable = ir.with_suffix('.exe' if os.name == 'nt' else '')
    commands = [
        ['-S', '-emit-llvm', ir.name, '-o', ir.with_suffix('.opt.ll').name],
        ['-S', ir.name, '-o', ir.with_suffix('.s').name],
        [ir.name, '-o', executable.name],
    ]
    for arguments in commands:
        command = [clang, '-Wno-override-module', f'-O{optimization}'] + arguments
        try:
            result = subprocess.run(command, cwd=ir.parent, capture_output=True, text=True)
        except OSError as error:
            raise BackendError(f'无法运行 clang：{error}') from error
        if result.returncode:
            raise BackendError(result.stderr + f'clang 执行失败，退出码 {result.returncode}')
    return executable


def run(executable):
    try:
        return subprocess.run([str(Path(executable).resolve())]).returncode
    except OSError as error:
        raise BackendError(f'无法运行可执行文件：{error}') from error
