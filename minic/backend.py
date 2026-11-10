"""clang handles optimization, assembly and linking; no third-party libraries."""
import os
from pathlib import Path
import subprocess


class BackendError(Exception):
    pass


def output_paths(ir):
    """Name all backend artifacts without inspecting or changing the filesystem."""
    ir = Path(ir)
    return dict(optimized=ir.with_suffix('.opt.ll'), assembly=ir.with_suffix('.s'),
                executable=ir.with_suffix('.exe' if os.name == 'nt' else ''))


def build(ir, optimization=2, clang='clang'):
    ir = Path(ir).resolve()
    # Relative explicit tool paths are relative to the caller, not the output dir.
    if os.path.dirname(clang):
        clang = str(Path(clang).resolve())
    outputs = output_paths(ir)
    executable = outputs['executable']
    # Explicit relative paths cannot be interpreted as options or response files.
    input_name = './' + ir.name
    commands = [
        ['-S', '-emit-llvm', input_name, '-o', './' + outputs['optimized'].name],
        ['-S', input_name, '-o', './' + outputs['assembly'].name],
        [input_name, '-o', './' + executable.name],
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
