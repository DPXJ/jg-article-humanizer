# 镜哥文章拟人化改写 Skill

`jg-article-humanizer` 用于对已经完成的中文文章初稿进行第二遍编辑。它保留事实、观点、证据图片和关键排版，重点恢复真实工作场景、口述思路、段落呼吸和作者个人判断。

## 主要能力

- 支持短图文 `flow`、公众号长文 `longform` 和结构锁定 `strict` 三种格式模式；
- 从用户的连续修改中提取当篇作者覆盖规则，避免旧表达在后续版本中回退；
- 优化章节过渡、案例叙事、段落节奏和收尾逻辑；
- 锁定专名、数据、链接、引语、Slogan、图片和关键样式；
- 按镜哥当前写作偏好，在每篇文章中加入恰好 3 处安全、随机的文字毛边，包括用户确认的近音混用或中英文间距毛边；
- 提供格式保真和常见语言回退检查脚本。

## 安装与使用

将本目录放在 Codex 的技能目录：

```bash
~/.codex/skills/jg-article-humanizer
```

在任务中明确调用：

```text
使用 $jg-article-humanizer 对这篇初稿做拟人化二改。
```

该 Skill 只用于已有初稿的真人化二改，不负责从零起稿或补充未经素材支持的事实。

## 验证

检查 Skill 结构：

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

检查改写前后的格式保真：

```bash
python3 scripts/verify_format_preservation.py original.md rewritten.md --mode auto
```

检查常见语言回退：

```bash
python3 scripts/lint_humanized_article.py rewritten.md
```

运行格式校验单元测试：

```bash
python3 -m unittest discover -s tests -v
```

语言脚本只提供风险提示。事实一致性、作者覆盖规则和三处随机文字毛边仍需在交付前人工复核。
