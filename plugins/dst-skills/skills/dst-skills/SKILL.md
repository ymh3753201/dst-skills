---
name: dst-skills
description: Use whenever a user supplies product images and wants multimodal product analysis, professional ecommerce visual strategy, marketplace listing images, detail-page graphics, SKU or campaign images, or model-native ecommerce image generation and review for any platform or market. This skill must still create commercially rich copy and executable art direction when product parameters are incomplete, without inventing product facts.
---

# dst-skills

把任意商品素材转成真正帮助购买决策的专业电商套图。Codex 必须同时扮演电商视觉策略总监、商业摄影指导、商品文案策划和商品身份审核者：先多模态读图并设计整套视觉策略，用户一次确认后，再由当前图像模型完成每一张成图、复核和返工。

## 不变底线

1. 最终消费者图片中的商品、场景、文字、图标和标注由图像模型生成；脚本只做记录、合同检查和验收 Contact Sheet。
2. 文字错误、商品漂移、信息贫乏或版式不专业时，继续图像编辑或重生成；不交付占位图或“建议人工后期”。
3. 平台要求无附加文案的搜索首图保持无字；其他页面不得因参数不足而退化成“商品静物＋两行大字”。
4. AI 可基于参考图渲染新角度、人物和场景，但不能把推断参数、材质、功能、配件或服务写成商品事实。
5. 不宣称平台后台通过，除非真实上传并回读验证。

## 1. 多模态素材诊断

查看全部商品图、包装、Logo、参数、细节、SKU、模特和风格参考。逐个记录 `role` / `proves` / `limitations`，再写出商品身份锁定、原图问题和设计机会。身份锁定要具体到轮廓、部件数量与位置、结构分区、Logo/接口、缝线、颜色和比例，不只写“保持一致”。

## 2. 平台与图片落点

**一个平台不是一种尺寸。** 查询当前平台后，把搜索首图、方形图库、3:4 主图、SKU、详情模块和活动图分别建立 `placement`，逐项记录用途、数量、比例、选定像素、依据和 `research_ids`。公开资料没有精确像素时标记“设计建议”，不冒充后台硬规则。

为 Image 2 选择可直接生成的精确尺寸；实际像素不合格时由模型按可执行规格重做，不通过脚本裁切、缩放或补边伪装完成。

## 3. 事实文案与安全商业文案

**缺参数不等于缺文案。** 将文案分两层：

- 事实文案：`product_fact` / `visual_fact` / `platform_fact`。参数、功能、材质、适配、配件和服务必须绑定已批准的 `fact_ids`。
- 安全商业文案：`safe_commercial` / `scenario_narrative` / `category_education` / `buyer_guidance`。可基于可见设计语言、审美利益、生活情绪、类目认知和买家引导补齐，但不得暗示未证实性能。

每页 `copy` 使用 `headline` / `subheadline` / `supporting_points` / `microcopy` 结构。除无字首图外，通常需要主标题、利益副标题和至少两条支撑信息；不用页面名称冒充销售文案。详见 [prompting.md](references/prompting.md)。

安全商业文案仍以正向商品理解和审美利益为主。风险声明放进 `microcopy`；没有用户或平台明确需要时，整套图中纯买前核对/风险清单页默认最多一张，不能用多页免责声明替代商品价值。

## 4. 缺口分级，不再全部卡死

**缺失不等于超出范围。** `out_of_scope` 仍只能用于用户明确排除或落点确实不需要的内容。对 `blocking` 增加 `blocking_scope`：

- `project`：商品身份不清、受监管信息不安全等，项目保持 `draft` 并阻止全部生图。
- `claim`：只阻止对应参数或功能文案；使用 `safe_fallback` 生成证据安全页面。
- `acceptance`：可生成安全套图，但不得声称商业证据完整。

有 `claim` / `acceptance` 缺口时，`delivery_scope` 使用 `evidence_safe`，`commercial_completeness` 使用 `evidence_safe_limited`。

只收集会改变商品身份、平台落点、事实口径或验收结论的关键缺口，并集中询问用户一次；其余信息由安全商业表达补齐。

## 5. 购买决策与视觉总纲

先建立买家决策地图，列出 5—10 个买家问题，覆盖**五个核心决策维度**：商品识别、使用/适配、证据、规格选择、风险/信任。再确定目标买家、购买动机、购买阻力、核心定位、创意概念、信息层级、色彩、字体、光线和版式语法。

专业完整套图默认不少于 8 张，至少四种 `composition_type`，场景与收束页不超过一半。每页都写 `primary_decision`、**每页独特证据** `unique_evidence`和不可被其他页替代的购买价值；**同一主要决策最多两页**。事实不足时不能用更多场景图填满数量。完整方案必须写入 `plan.md`。

## 6. 将页面写成可执行蓝图

每页 `visual_brief` 不再是“高级、简约”之类风格口号，而是布局蓝图：`product_scale`、`product_multiplicity`、`focal_zone`、`copy_zone`、`hierarchy`、`graphic_devices`、`lighting`、`depth`、`information_density`、`composition_rationale`和 `content_modules`。`product_multiplicity` 必须说明本页出现几套售卖商品，以及多角度/步骤重复视图是否只代表同一件商品，防止模型把开合对照生成成两件商品。

`detail` / `diagram` / `process` / `comparison` / `package` / `trust` 必须真实包含局部证据、标注、图解、流程、对比、清单或信任证据，不得把静物场景只标记成 `detail` 来绕过检查。

## 7. 确认前专业度预审与提示词编译

完成结构化方案后运行：

```bash
python3 scripts/compile_prompts.py path/to/project.json --write
python3 scripts/validate_project.py path/to/project.json --schema-only
```

最终提示词必须包含 `【页面任务】` `【商品身份】` `【构图蓝图】` `【文案系统】` `【视觉执行】` `【负面约束】`六部分。提示词应先提供充足的正向创意和信息关系，再列真正重要的禁止项。

## 8. 一次确认与不可事后改写

确认后的数量、页面任务、事实、核心文案、商品身份和 placement 是生图依据。确认时记录 `plan_sha256` 和 `execution_manifest_sha256`。生成记录必须包含 `attempt`、`generated_at`、`prompt_sha256`和同一 `plan_sha256`；生成时间必须晚于确认时间。确认后如果页面、文案、提示词或方案发生实质变化，重新确认，不得事后补写时间或替换方案。

## 9. 生图、视觉验收与交付

生成前读取当前 `imagegen` Skill，将参考素材和编译后的逐页提示词直接交给 Codex 图像生成/编辑能力。错字可局部编辑；商品、构图、信息层级或商业价值失败时整页重做。

逐张原图复核后再制作 Contact Sheet。`review.set_checks` 除商业覆盖、落点差异、构图多样性、文字融合和商品一致性外，还必须检查 `copy_richness`、`buyer_value`、`prompt_fidelity`和 `claim_safety`。每页对商业价值、文案层级、商品一致性、提示词忠实度和视觉完成度打 1—5 分；任一项低于 4 分不得 `pass`。“人工复核通过”之类空话不是证据。

交付前运行：

```bash
python3 scripts/validate_project.py path/to/project.json --project-dir path/to/project
python3 scripts/build_contact_sheet.py path/to/project.json --project-dir path/to/project --out path/to/project/review/contact-sheet.jpg
python3 scripts/validate_skill_release.py --full
```

同一执行者只能标记 `manual_review`；最终 `accepted` 需要用户或独立复核者确认。交付时明确当前只到工程验证、真实成图验证、用户验收还是平台后台验证。
