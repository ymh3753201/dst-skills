# 专业电商视觉方案

> 本文件必须保存为项目目录中的 `plan.md`。它是给用户确认的完整方案；`project.json` 只是给 Codex 验证和执行的结构记录。

## 1. 项目状态与结论

- 项目状态：`draft` / `planned`
- 能否请用户确认生成：能 / 不能
- 一句话原因：
- 当前交付：平台、图片落点、数量、规格和是否包含详情页
- 交付范围：`full_evidence` / `evidence_safe`

## 2. 素材诊断

| 素材 | 角色 | 能证明什么 | 局限/原图问题 | 计划用途 |
|---|---|---|---|---|
| asset-01 | 商品身份主参考 / 角度 / 细节 / 包装 / SKU / 模特 / 场景 / 风格 |  |  |  |

- 商品与品类：
- 商品身份锁定：主体轮廓、部件数量和位置、结构分区、颜色、Logo/接口、缝线、比例
- 原图主要问题：
- 可通过 AI 改造的机会：
- 不能由 AI 推断的商品事实：

## 3. 事实证据表

| fact_id | 事实内容 | evidence status | claim scope | approved for copy | 来源 | 备注/待确认 |
|---|---|---|---|---|---|---|
| fact-01 |  | verified / source_claim / ambiguous / missing | 该事实究竟证明什么 | true / false | asset / user / research |  |

规则：

- `ambiguous` 和 `missing` 必须是 `approved for copy = false`。
- 数字必须说清主体与口径，例如“充电盒电池容量”、“单次续航”或“含充电盒综合续航”。
- 佩戴方式、操作、接口、材质、功能、适配和服务是商品事实，不得写成 AI 创意推断。

## 4. 定位与创意总纲

- 目标买家：
- 购买动机：
- 购买阻力：
- 核心定位：
- 创意概念/视觉主题：
- 信息层级：第一印象 → 利益与证据 → 规格/选购/信任
- 风格、色彩、字体、光线和版式语法：
- 商品一致性规则：

### 文案策略

- 原则：缺参数不等于缺文案；未证实性能不能被商业表达暗示。
- 事实文案规则：参数、材质、功能、认证、服务和适配必须绑定事实 ID。
- 安全商业文案支柱：可见设计语言 / 审美利益 / 场景叙事 / 类目教育 / 买家引导。
- 不同落点的信息密度：搜索首图低、图库中、详情中高。
- 禁止推断：

## 5. 平台依据与验证层级

| 证据 ID | 来源类型 | 链接/用户资料 | 核对日期 | 对本项目的结论 |
|---|---|---|---|---|
| platform-01 | official / store_theme / user |  |  |  |

- `platform_validation`：`design_recommendation` / `backend_verified`
- 平台公开硬规则：
- 店铺主题或当前后台要求：
- 可执行设计建议：
- 上线前仍需复核：

## 6. 平台图片落点与规格

一个平台不是一种尺寸。逐个真实落点建立 `placement_id`。
常见落点包括：方形搜索首图/图库、3:4 主图/导购图、纵向详情模块、SKU 与活动图。

| placement_id | 平台字段/图片落点 | surface | 数量 | 比例 | 选定像素 | 尺寸依据 | research_ids |
|---|---|---|---:|---|---|---|---|
| square-main | 搜索首图/方形图库 | search_main |  | 1:1 | 1200×1200 | 平台规则 / 店铺要求 / 设计建议 | platform-01 |
| portrait-detail | 竖向主图/详情模块 | detail |  | 3:4 | 1200×1600 |  | platform-01 |

完整套图至少两个 placement 和两种选定尺寸；用户明确只做一个落点时才能简化。

## 7. 买家决策地图

| decision_id | 买家问题 | decision dimension | claim type | 优先级 | 状态 | blocker scope | 安全替代表达 | 依据 | fact_ids | page_ids | 原因/待补信息 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| decision-01 |  | identity / usage_fit / proof / selection / trust / benefit / risk / platform | product_fact / platform_fact / creative_simulation / style_recommendation / missing_fact / scope_exclusion | high / medium / low | covered / blocking / out_of_scope | none / claim / acceptance / project |  | visible / user / research / model_inferred / missing / out_of_scope |  |  |  |

### 商业完整度

- 商品识别 `identity`：已覆盖 / 缺失
- 使用与适配 `usage_fit`：已覆盖 / 缺失
- 可见证据 `proof`：已覆盖 / 缺失
- 规格选择 `selection`：已覆盖 / 缺失
- 风险与信任 `trust`：已覆盖 / 缺失
- 当前所有 `blocking`：
- `out_of_scope` 的用户明确排除证据 `scope_ref`：

只有 `project` 级阻断必须让整个项目保持 `draft`。`claim` 级阻断只禁止对应事实文案，使用已明确的安全替代表达后仍可形成 `evidence_safe` 完整方案；`acceptance` 级阻断允许生成候选图，但未补证据前不能进入最终验收。

## 8. 逐页方案

| 页 | placement_id / surface | primary decision | unique evidence | 构图类型 | 页面任务 | 文案系统 | 版式蓝图 | claim_fact_ids | 参考素材/事实 | 像素与依据 |
|---|---|---|---|---|---|---|---|---|---|---|
| 01 |  |  | 本页唯一提供的证据 | hero / scene / detail / angles / diagram / process / comparison / package / trust / closing |  | 标题＋副标题＋至少两条辅助信息；逐条标注 fact 或 safe | 商品比例、商品数量/重复视图、视觉焦点、文案区、信息层级、视觉装置、光线、景深、信息密度、内容模块 |  |  |  |

每页必须有不可被其他页替代的证据。确认态完整套图中，同一 `primary decision` 最多两页。不得用重复场景、重复续航或重复细节页填数量。

除平台要求无字的搜索首图外，每页文案必须采用结构化角色：`headline`、`subheadline`、`supporting_points`、`microcopy`。每条文案还要标明类型和事实绑定。详情页至少包含一种真实信息模块，例如局部放大、步骤、清单、对比、适配或买前指引；不能只是竖向生活场景。

## 9. 风险、待补问题与一次确认

- AI 渲染的新角度、人物或场景：
- 无证据不能表达的参数、材质、功效或服务：
- 当前仍为 `draft` 的原因：
- 集中向用户补充的问题：
- 用户确认结果：
- `plan.md` SHA-256：
- 执行清单 SHA-256：
- 执行锁定：确认后的数量、页面任务、事实、核心文案、商品身份和 placement 是生图依据；实质变化需更新方案并重新确认。

## 10. 确认前专业度预审

1. 素材诊断是否指出具体问题和改造机会。
2. 五个核心决策维度是否真正覆盖。
3. 参数主体、口径和佩戴/使用事实是否有证据。
4. 是否把缺失错写成 `out_of_scope`。
5. 多个 placement、数量、比例、像素和依据是否逐项记录。
6. 每页是否有独立任务、主要决策和唯一证据。
7. 事实文案是否与已批准的 `claim_fact_ids` 对应；参数不足时是否用安全商业文案补齐商业内容。
8. 每页是否形成可执行版式蓝图，是否避免“商品静物＋两行大字”。
9. 提示词是否包含页面任务、商品身份、构图蓝图、文案系统、视觉执行和负面约束六部分。
10. 完整 `plan.md` 和提示词是否已写入项目，并运行：

```bash
python3 scripts/validate_project.py path/to/project.json --schema-only
python3 scripts/compile_prompts.py path/to/project.json --write
```

再次校验通过后，记录真实方案与执行清单哈希。只有 `planned` 项目出现 `PROJECT VALIDATION OK`，并通过上述专业预审，才可请用户一次确认并生图；不能事后补写确认。
