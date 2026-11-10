#!/usr/bin/env python3
"""计划文件结构检查（AC00 的机器可核对部分）。

用法：python3 scripts/check_plan.py doc/task1
只读检查，不修改任何文件。全部通过时退出码 0，否则为 1。
它只核对结构与编号是否闭合，不能代替对内容的人工审阅。
"""
import re
import sys
from pathlib import Path

SPEC_HEADINGS = ["目标", "范围", "规则", "AC测试", "假设"]
AC_HEADER = "| AC | Rule | Input | Expected result |"


def expand(text: str, prefix: str) -> set[str]:
    """提取 R01、AC03 这类编号，并展开 R04–R08 这样的区间。"""
    found: set[str] = set()
    for lo, hi in re.findall(rf"{prefix}(\d\d)\s*[–\-至]\s*{prefix}(\d\d)", text):
        found.update(f"{prefix}{n:02d}" for n in range(int(lo), int(hi) + 1))
    found.update(f"{prefix}{n}" for n in re.findall(rf"{prefix}(\d\d)", text))
    return found


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    task_dir = Path(sys.argv[1])
    problems: list[str] = []
    texts = {}
    for name in ("spec", "design", "tasks", "checklist"):
        path = task_dir / f"{name}.md"
        if not path.is_file():
            problems.append(f"缺少文件 {path}")
            texts[name] = ""
        else:
            texts[name] = path.read_text(encoding="utf-8")
    spec, tasks, checklist = texts["spec"], texts["tasks"], texts["checklist"]

    # 1. spec 的二级标题
    headings = re.findall(r"^## (.+)$", spec, flags=re.M)
    print(f"spec 二级标题：{headings}")
    if headings != SPEC_HEADINGS:
        problems.append(f"spec 二级标题应为 {SPEC_HEADINGS}")

    # 2. 规则编号与依据
    rules = re.findall(r"^- (R\d\d) \[([^\]]*)\]：", spec, flags=re.M)
    rule_ids = [r for r, _ in rules]
    print(f"规则：{len(rule_ids)} 条（{rule_ids[0] if rule_ids else '-'} 至 {rule_ids[-1] if rule_ids else '-'}）")
    if rule_ids != [f"R{n:02d}" for n in range(1, len(rule_ids) + 1)]:
        problems.append("规则编号不连续或有重复")
    for rid, basis in rules:
        if not basis.strip() or "待填写" in basis:
            problems.append(f"{rid} 缺少依据")

    # 3. AC 表
    if AC_HEADER not in spec:
        problems.append("spec 缺少规定的 AC 表头")
    ac_rows = re.findall(r"^\| (AC\d\d) \| ([^|]*) \|", spec, flags=re.M)
    ac_ids = [a for a, _ in ac_rows]
    print(f"AC：{len(ac_ids)} 项（{ac_ids[0] if ac_ids else '-'} 至 {ac_ids[-1] if ac_ids else '-'}）")
    if ac_ids != [f"AC{n:02d}" for n in range(len(ac_ids))]:
        problems.append("AC 编号不从 AC00 连续排列或有重复")
    covered: set[str] = set()
    for ac, rule_cell in ac_rows:
        refs = expand(rule_cell, "R")
        if ac != "AC00" and not refs:
            problems.append(f"{ac} 没有引用规则")
        for ref in sorted(refs - set(rule_ids)):
            problems.append(f"{ac} 引用了不存在的 {ref}")
        covered |= refs
    for rid in rule_ids:
        if rid not in covered:
            problems.append(f"{rid} 没有被任何 AC 覆盖")

    # 4. checklist 与 AC 一一对应
    check_ids = re.findall(r"^## (AC\d\d)\b", checklist, flags=re.M)
    print(f"checklist 小节：{len(check_ids)} 项")
    if check_ids != ac_ids:
        missing = sorted(set(ac_ids) - set(check_ids))
        extra = sorted(set(check_ids) - set(ac_ids))
        problems.append(f"checklist 与 spec 的 AC 不一致：缺少 {missing}，多出 {extra}，或顺序不同")

    # 5. tasks 的引用
    task_ids = re.findall(r"^- \[[ x]\] (T\d+-\d\d)", tasks, flags=re.M)
    print(f"任务阶段：{task_ids}")
    if len(task_ids) != len(set(task_ids)) or not task_ids:
        problems.append("tasks 阶段编号缺失或重复")
    task_acs = expand(tasks, "AC")
    for ref in sorted(task_acs - set(ac_ids)):
        problems.append(f"tasks 引用了不存在的 {ref}")
    for ac in ac_ids:
        if ac not in task_acs:
            problems.append(f"{ac} 没有被任何任务阶段关联")
    task_rules = expand(tasks, "R")
    for ref in sorted(task_rules - set(rule_ids)):
        problems.append(f"tasks 引用了不存在的 {ref}")
    for rid in rule_ids:
        if rid not in task_rules:
            problems.append(f"{rid} 没有被任何任务阶段关联")

    # 6. 勾选状态与“未执行”字样不得矛盾
    sections = re.split(r"^## ", checklist, flags=re.M)[1:]
    done = []
    for sec in sections:
        m = re.match(r"(AC\d\d)", sec)
        box = re.search(r"^- \[([ x])\] (.*)$", sec, flags=re.M)
        if not m or not box:
            continue
        if box.group(1) == "x":
            done.append(m.group(1))
            if box.group(2).startswith("未执行"):
                problems.append(f"{m.group(1)} 已勾选但状态写着未执行")
        elif not box.group(2).startswith(("未执行", "未通过", "部分通过", "阻塞")):
            problems.append(f"{m.group(1)} 未勾选，状态应以 未执行/未通过/部分通过/阻塞 开头")
    print(f"checklist 已勾选：{done if done else '无'}")

    # 7. 残留占位符
    project_root = task_dir.resolve().parent.parent
    for path in [task_dir / f"{n}.md" for n in ("spec", "design", "tasks", "checklist")] + [
        project_root / "README.md",
        project_root / "doc" / "project-config.md",
    ]:
        if path.is_file() and "{{" in path.read_text(encoding="utf-8"):
            problems.append(f"{path} 中残留占位符 {{{{…}}}}")

    if problems:
        print(f"发现 {len(problems)} 个问题：")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("结构检查通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
