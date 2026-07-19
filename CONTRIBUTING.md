# Contributing

感谢你帮助改进 dst-skills。

## 开发流程

1. 从 `main` 创建短期分支。
2. 只提交与本次修改有关的文件，不提交客户素材、生成项目、缓存或密钥。
3. 修改 Skill 行为时同步更新测试、示例和 `CHANGELOG.md`。
4. 本地完成全部检查后再提交 Pull Request。

```bash
python3 -m pip install -r plugins/dst-skills/skills/dst-skills/requirements.txt
python3 plugins/dst-skills/skills/dst-skills/scripts/validate_skill_release.py --full
python3 scripts/validate_repository.py
python3 scripts/package_skill.py --output dist/dst-skills.skill
```

## Pull Request 要求

- 标题使用 `feat(scope): summary`、`fix(scope): summary` 或 `docs(scope): summary`。
- 说明修改目的、主要变化、测试证据和风险边界。
- 不降低商品事实、用户确认、商品一致性或视觉验收门槛。
- CI 全部通过后才能合并。

## 版本规则

项目使用语义化版本：

- 修复兼容问题：补丁版本。
- 增加兼容能力：次版本。
- 更改项目合同或出现不兼容结构：主版本。

版本变化必须同步更新 Skill 的 `VERSION`、`CHANGELOG.md` 和插件 `plugin.json`。
