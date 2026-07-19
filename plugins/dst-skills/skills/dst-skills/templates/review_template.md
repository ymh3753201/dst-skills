# 电商套图视觉复核

- 项目：
- 复核状态：manual_review / accepted
- 复核者：same_agent / user / independent
- Contact Sheet：

## 单页评分

| 页 | commercial value | copy hierarchy | product consistency | prompt fidelity | visual polish | 具体证据 | 结论 |
|---|---:|---:|---:|---:|---:|---|---|
| page-01 | 1—5 | 1—5 | 1—5 | 1—5 | 1—5 | 写明原图可见位置、文字和商品细节 | pass / redo |

任一评分低于 4 分必须返工。“人工原图复核通过”“整套专业”或执行者自己填写 `pass` 都不是合格证据。

## 整套判断

| `set_check` | 状态 | Contact Sheet 可见证据 |
|---|---|---|
| `commercial_coverage` 商业信息覆盖 | pass / redo | 哪些页覆盖识别、利益、证据、选购、风险与信任 |
| `surface_difference` 落点差异 | pass / redo | 不同 placement 的尺寸、构图和密度差异 |
| `composition_diversity` 构图多样性 | pass / redo | 至少四种真实构图及页号 |
| `text_integration` 文字融合 | pass / redo | 逐字正确、层级清楚、无浮贴和 PPT 卡片 |
| `product_consistency` 商品一致性 | pass / redo | 颜色、结构、Logo、接口、比例与配件对照 |
| `copy_richness` 文案完整度 | pass / redo | 非无字首图具备标题、副标题和至少两条支撑信息 |
| `buyer_value` 买家价值 | pass / redo | 每页怎样回答具体购买问题，排除空泛口号 |
| `prompt_fidelity` 方案忠实度 | pass / redo | 成图落实已确认的机位、版式、文案和信息模块 |
| `claim_safety` 事实安全 | pass / redo | 未证实参数未出现，事实文案均可追溯 |

- 是否存在商品静物＋两行大字或换模板式重复页：
- placement、数量、尺寸和宽高比是否符合已记录依据：
- 下一步：图像编辑 / 整页重做 / 进入用户验收
