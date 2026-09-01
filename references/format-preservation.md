# 格式保真规则

拟人化改写按内容类型使用三种格式模式：

- `flow`：小绿书、朋友圈、即刻和普通短图文。保护平台外壳，允许为真人节奏拆段、并段和插入独立短句。
- `longform`：公众号、博客和 1200 字以上 Markdown 配图长文。保护证据与排版节点，允许章节内部拆段、并段和补充过渡。
- `strict`：HTML、代码密集内容、局部改写和用户明确要求结构不动的内容。保护完整结构，只替换允许改写的文字。

校验脚本的 `auto` 模式会把「由单个外层 fenced code block 包裹，并使用全角空格分段」的内容识别为 `flow`；包含 Markdown 标题且正文达到 1200 个中日韩字符的内容识别为 `longform`；其他内容使用 `strict`。

## 小绿书代码块

- 输入只有一个无语言标记 fenced code block，输出也只能有一个相同代码块；
- 围栏外保持零文字；
- 段落间继续使用仅含全角空格 `　` 的占位行；
- 不把占位行换成普通空行，也不增加 Markdown 标题、列表、加粗或 Emoji；
- 可以拆分、合并或增加自然段，也可以把关键问句、吐槽或判断独立成段；
- 不改变核心事实顺序，不把新增段落写成新的事实或经历。

## Markdown 长文

`longform` 模式保持以下项目原位、原样：

- fenced code block 及语言标记；
- 标题层级、标题顺序和标题文本；
- 图片语法、图片地址和图注位置；
- 链接地址、HTML 注释、分隔线；
- 引用、列表、加粗、高亮等标记的数量和范围；
- fenced code block 及语言标记；
- 章节顺序和媒体的相对顺序。

允许在同一章节内拆分、合并普通叙述段落，或增加不含新事实的过渡和判断。不得跨标题移动段落，不得把图片、链接、列表或重点样式移入其他章节。允许改写标题文字或图注文字的前提是用户把它们包含在改写范围内；不得改变其语法和位置。

`strict` Markdown 继续保持普通空行、段落数量和完整行骨架。

## HTML

只修改可见文本节点。所有标签名、嵌套关系、属性、class、id、style、src、href、data 属性和注释保持原样。正文中夹有脚本或样式时完全跳过 `script`、`style`、`pre`、`code` 内容。

## 局部标注

用户指定句子、段落或区间时，只返回原文整体并替换该区间；范围外逐字保持。用户只要求返回改写片段时，沿用片段本身的格式，不补上下文。

## 机器检查

运行：

```bash
python3 scripts/verify_format_preservation.py original.md rewritten.md --mode auto
```

也可以显式指定：

```bash
python3 scripts/verify_format_preservation.py original.md rewritten.md --mode flow
python3 scripts/verify_format_preservation.py original.md rewritten.md --mode longform
python3 scripts/verify_format_preservation.py original.md rewritten.md --mode strict
```

`flow` 检查围栏、代码块外零文字、全角空格分段协议、纯文本限制以及图片和链接资源；不比较段落数量。`longform` 检查标题、媒体、链接、重点标记和章节顺序，允许普通段落骨架变化。`strict` 继续比较完整段落骨架。检查器不能判断事实、语义或三处毛边是否正确，需要人工复核。
