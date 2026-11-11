# AC24 浏览器验证尝试（未完成）

日期：2026-11-11。执行者：Codex；不是用户的人工目视，不作为 AC18 人工验收。

- 环境：macOS 26.5.1 arm64；浏览器控制目标为 ChatGPT 内置浏览器（`iab`）。页面未能加载，因此没有取得浏览器内核名称/版本或页面 UA，不推定为 Safari/Chrome 的某个版本。
- 页面：`doc/task1/evidence/t107/demo/ast.html`，由 `examples/demo.mc` 编译得到；准备命令、Python 路径、退出码、HTML SHA-256 在 [browser-prepare.json](browser-prepare.json)。页面文件本身未经测量脚本或其他改写。
- 操作：浏览器 viewport 接口成功设置 `{width: 1280, height: 900}`；随后请求以 `file://` URL 打开页面。
- 实际返回：浏览器安全策略拒绝该动作，提示 “The requested URL protocol is not allowed. Allowed protocols: \"http:\", \"https:\".”，并禁止通过替代浏览器表面或间接执行绕过该拒绝。
- 结果：页面没有打开，脚本没有在浏览器中执行，没有按钮点击、页面截图、版本信息或几何数据。没有转换协议或切换其他控制通道绕过策略。随后调用 viewport `reset()` 成功恢复默认尺寸。
- 浏览器工具返回拒绝信息，不是 shell 进程，没有可记录的进程退出码；不可写成退出 0。

| 状态 | 根矩形边界 | 容器边界 | scrollWidth | clientWidth | 判定 |
|---|---|---|---|---|---|
| 刚打开 | 未取得 | 未取得 | 未取得 | 未取得 | 未执行 |
| 点击“适应宽度” | 未取得 | 未取得 | 未取得 | 未取得 | 未执行 |
| 点击“原始大小” | 未取得 | 未取得 | 未取得 | 未取得 | 未执行 |

自动部分：`test_ac24_controls_offline_nodes_and_deterministic_html` 已通过，核对容器/按钮、默认按钮状态、自包含、结点数及两次输出一致；这不执行 JavaScript，也不能证明实际定位、缩放或字体重排后的效果。

结论：AC24 保持未勾选。后续须在可访问该本地文件的真实浏览器中完成三状态实测，记录浏览器及版本、1280 像素宽度、根矩形和容器边界、scrollWidth/clientWidth、适应宽度时全部结点的可见性、原始大小的 SVG 宽度与根居中误差。不得把既往 Safari 的 AC18 记录当成本次页面的 AC24 结果。
