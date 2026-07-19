# dst-skills

面向 Codex 的通用电商视觉生产 Skill。它读取用户提供的商品图，完成多模态商品分析、平台多落点规格规划、整套电商视觉方案、逐页生图提示词编译、参考图生成和最终视觉验收。

它不绑定某个商品或某个平台。不同平台会根据搜索首图、商品图库、SKU、详情页和活动图等真实落点分别设计数量、比例和尺寸，而不是把整套图片套进一种规格。

## 核心能力

- 分析商品图中的轮廓、结构、颜色、部件、材质表现、包装与可见文字。
- 将已验证商品事实与安全商业文案分开；资料不足时仍能补齐审美利益、场景叙事、类目教育和买家引导。
- 建立买家决策地图，覆盖商品识别、使用与适配、证据、规格选择、风险与信任。
- 为每一页输出明确的商品占比、焦点、文案区、信息层级、光线、景深、内容模块与商品数量规则。
- 把确认后的方案编译为六段式图像提示词，交给 Codex 图像生成能力逐页执行。
- 检查商品变形、错字、文案贫乏、页面重复、提示词偏离和不实宣传；不合格页面必须返工。
- 区分工程测试通过、真实成图通过、用户验收和平台后台验证，避免混淆完成状态。

## 工作流程

1. 读取全部商品素材并锁定商品身份。
2. 查询目标平台的当前公开规则，拆分多个图片落点和规格。
3. 整理商品事实、缺失信息和可安全使用的商业表达。
4. 输出完整视觉总纲、买家决策地图和逐页设计蓝图。
5. 运行结构预审，把方案一次性交给用户确认。
6. 确认后按逐页提示词调用 Codex 图像生成能力。
7. 逐张复核并返工，最后生成 Contact Sheet 和验收记录。

## 安装

### Codex 插件安装（推荐）

```bash
codex plugin marketplace add ymh3753201/dst-skills
codex plugin add dst-skills@dst-skills
```

安装后建议打开新任务，让 Codex 重新读取 Skill。示例：

```text
用 $dst-skills 分析这些商品图，为京东设计一整套专业商品图。先给完整视觉方案和每个落点的规格，不要立即生图。
```

### 直接复制 Skill

```bash
git clone https://github.com/ymh3753201/dst-skills.git
mkdir -p ~/.agents/skills
rsync -a --delete dst-skills/plugins/dst-skills/skills/dst-skills/ ~/.agents/skills/dst-skills/
```

旧版 Codex 如果仍使用 `~/.codex/skills`：

```bash
mkdir -p ~/.codex/skills
rsync -a --delete dst-skills/plugins/dst-skills/skills/dst-skills/ ~/.codex/skills/dst-skills/
```

不要只复制 `SKILL.md`。完整能力还依赖 `references/`、`templates/`、`scripts/`、`tests/`、`examples/` 和 `evals/`。

## 使用示例

只做方案：

```text
用 $dst-skills 读取我提供的商品图，为淘宝规划完整套图。请区分搜索首图、商品图库、SKU 和详情页，逐页写清文案、构图与尺寸，先不要生图。
```

确认后生成：

```text
我确认这套方案。请严格按已确认的每页文案和视觉蓝图生成全部图片，并逐张检查商品一致性、错字和商业完成度。
```

## 事实与合规边界

- 允许依据商品图补充可见设计、审美利益、使用氛围、类目认知和买家引导。
- 参数、功能、材质、适配、配件、服务和功效必须有用户资料或可靠证据。
- 搜索首图若平台要求无附加文案，应保持无字。
- AI 可以基于参考图渲染新角度、人物和场景，但不能改变商品结构或把推断写成事实。
- 没有真实上传并回读验证时，不宣称平台后台已经通过。

## 本地验证

需要 Python 3.11+：

```bash
python3 -m pip install -r plugins/dst-skills/skills/dst-skills/requirements.txt
python3 plugins/dst-skills/skills/dst-skills/scripts/validate_skill_release.py --full
python3 scripts/validate_repository.py
python3 scripts/package_skill.py --output dist/dst-skills.skill
```

当前 v8.2.0 的完整回归套件包含 155 项测试。CI 会再次执行测试、仓库结构检查和安装包自检。

## 项目结构

```text
dst-skills/
├── .agents/plugins/marketplace.json
├── .github/workflows/ci.yml
├── plugins/dst-skills/
│   ├── .codex-plugin/plugin.json
│   └── skills/dst-skills/
├── scripts/
├── CONTRIBUTING.md
├── SECURITY.md
└── LICENSE
```

## 贡献与安全

提交修改前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全问题请按 [SECURITY.md](SECURITY.md) 私下报告，不要在公开 Issue 中附带密钥、未公开商品资料或客户素材。

## 许可证

[MIT License](LICENSE)
