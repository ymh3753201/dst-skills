# 模型原生电商图文案与提示词

## 参数不足时仍要完成商业表达

不能把“不编造参数”执行成“只写品类名和场景名”。文案分为：

- `product_fact` / `visual_fact` / `platform_fact`：事实文案，必须绑定已批准 `fact_ids`。
- `safe_commercial`：核心定位、可见设计语言、审美利益和消费者记忆点。
- `scenario_narrative`：日常节奏、情绪和生活代入，不暗示性能。
- `category_education`：帮买家看懂结构、角度、部件和选择方法的通用知识。
- `buyer_guidance`：下单前核对尺寸、型号、包装或服务的安全提示。

安全商业文案可以专业、有感召力，但不得使用“轻盈、稳固、舒适、耐用、高音质”等会暗示未证实性能的词。

## 结构化 `copy`

除平台无字搜索首图外，每页通常使用：

```json
{
  "headline": {"text": "环形轮廓，一眼看出不同", "kind": "safe_commercial", "fact_ids": []},
  "subheadline": {"text": "米白同色设计，从耳机到充电盒视觉更统一", "kind": "visual_fact", "fact_ids": ["fact-visible-product"]},
  "supporting_points": [
    {"text": "左右结构多角度看清", "kind": "category_education", "fact_ids": []},
    {"text": "圆润线条贯穿整套外观", "kind": "safe_commercial", "fact_ids": []}
  ],
  "microcopy": []
}
```

`headline` 提出一个明确价值，`subheadline` 解释为什么，`supporting_points` 提供至少两条可扫读的支撑信息。`microcopy` 只用于必要的规格、风险或注释，不为了填空而增加。

安全不等于把整套图写成免责声明。优先顺序是可见设计解读、商品结构教育、场景利益和选择帮助；风险边界尽量收进 `microcopy`。除非用户或平台确实需要，纯买前核对/风险清单页默认最多一张。

## 布局蓝图

每页 `visual_brief` 必须具体记录：

- `product_scale`：商品占比与呼吸空间；
- `product_multiplicity`：实际展示几套商品；多角度、步骤或局部图是否只是同一商品的重复视图；
- `focal_zone` / `copy_zone`：主焦点和文案区；
- `hierarchy`：主标题、副标题、支撑信息的层级；
- `graphic_devices`：弧线、局部放大、标注线、色块或图形隐喻；
- `lighting` / `depth`：商业光线和前中后景关系；
- `information_density`：`low` / `medium` / `medium_high`；
- `composition_rationale`：为什么这样设计能回答买家问题；
- `content_modules`：本页真实包含的信息模块。

`detail` 页不能只有 `lifestyle_scene`，至少包含 `macro_proof` / `callout` / `material_proof` / `structure_proof` 之一。其他信息型页使用 `decision_diagram` / `buyer_guidance` / `process_steps` / `comparison_matrix` / `package_inventory` / `trust_evidence` 等真实模块。

## 六段式可执行提示词

先由 Codex 完成文案和布局蓝图，再运行 `python3 scripts/compile_prompts.py project.json --write`。每页最终提示词必须包含：

1. `【页面任务】`：尺寸、placement、页面角色、买家问题和独特证据。
2. `【商品身份】`：参考图角色、身份摘要和不可变特征。
3. `【构图蓝图】`：商品占比、商品数量/重复视图、焦点、文案区、层级、模块和构图原因。
4. `【文案系统】`：逐字文案、文案类型、事实引用、字体气质和空间关系。
5. `【视觉执行】`：创意概念、风格、色彩、光线、层次、图形语言和信息密度。
6. `【负面约束】`：只保留商品身份、事实安全和廉价模板风险等关键禁止项。

生图前逐字检查所有 copy 都已进入提示词，并检查正向创意是否足以支撑页面；不用大量“不要”掩盖正向设计的缺失。

## 返工

- 局部错字且商品稳定：图像编辑替换文字。
- 文案层级、信息密度、商品或构图错误：带完整参考图和六段提示词整页重做。
- 不写“预留文字区”“后期添加”或“生成干净底图”。
