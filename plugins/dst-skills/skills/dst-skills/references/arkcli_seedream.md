# Ark CLI 与 Doubao Seedream 5.0 Pro 执行合同

当项目的 `generation_channel` 已锁定为 `arkcli_seedream_5_pro`，或默认 `codex_image_with_arkcli_fallback` 策略已记录真实 Codex 调用失败时，Ark 生图入口是 Ark CLI `+gen`，固定模型为 `doubao-seedream-5-0-pro-260628`。模型目录中的 `doubao-seedream-5-0-260128` 对应 Seedream 5.0 lite，不得混用，也不得把本文的规则强加给正常执行的 Codex 渠道。

## 每次执行前的三步核对

1. 用 `arkcli auth status --format json` 确认登录和 API Key 有效，不输出完整凭证。
2. 用 `arkcli resources list --modality image --format json` 查看当前 profile 的图片资源。Plan profile 可直接使用完整 Pro 模型 ID；Platform profile 必须选择一个 `ep-...` Endpoint，再用 `arkcli resources resolve <ep-id> --format json` 确认它处于 `Running` 且绑定完整 Pro 模型。没有匹配 Endpoint 时停止并取得部署授权。
3. 用 `arkcli models get doubao-seedream-5-0-pro-260628 --transform supported_params --format json` 读取当前参数能力，再调用 `arkcli +gen`。

Agent 发起每条 Ark CLI 命令时都要带共享 Skill 规定的调用来源环境变量。不得把 API Key 写进项目、日志或命令示例。

`arkcli api arkruntime.generate_images` 只允许在产品命令受当前 Platform 配置阻断时做独立文本生图诊断。它能证明 API Key 与 Pro 模型可调用，但不能证明 `+gen`、本地参考图上传和项目文件落地链路通过，不得用于正式套图记录。

## Seedream 5.0 Pro 图片合同

- 文生图、单图生图和多图生图均支持，参考图最多 10 张。
- 不支持 `sequential_image_generation`，所以完整套图必须逐页调用，不使用 `--image-count`、`--n` 或 `--sequential`。
- 输入图片支持 URL 或 Ark CLI 的 `--input @本地文件`；单图不超过 30MB，宽高比在 1:16—16:1 之间。
- 提示词硬上限为 400000 字符，但中文建议不超过 300 字、英文建议不超过 600 词。六段式提示词优先保证事实、商品身份、逐字文案和布局完整，再删除重复形容词。
- `guidance_scale`、工具调用和组图参数不受支持，不得传入。
- 默认只生成一张图。`response_format=url` 的链接 24 小时失效，必须依赖 Ark CLI 下载后的 `local_path` 保存长期产物。
- 必须显式传 `--watermark=false`。省略时请求体不含该字段，服务端会使用 `watermark=true` 默认值；裸 `--watermark` 同样表示开启。不得用脚本移除水印。

## 尺寸合同

支持两种方式，不能混用：

- 档位：`1K`、`1.5K`、`2K`，同时在提示词里明确 1:1、3:4、4:3、16:9、9:16 等用途和形状。
- 精确像素：`宽x高`，总像素必须在 921600—4624220 之间，宽高比必须在 1:16—16:1 之间。

例如 `1200x1200`、`1200x1600`、`2048x1024` 都符合精确像素合同；`512x512` 因总像素不足不合格。Seedream 5.0 Pro 没有“边长必须是 16 的倍数”的限制。

## 标准命令

```bash
ARKCLI_NO_UPDATE_NOTIFIER=1 \
ARKCLI_CALLER_TYPE=ai_agent \
ARKCLI_CALLER_NAME=codex \
ARKCLI_SKILL_NAME=arkcli-gen \
arkcli +gen \
  --model '<完整Pro模型ID或已绑定Pro的Endpoint-ID>' \
  --modality image \
  --size 1200x1600 \
  --output-format png \
  --response-format url \
  --watermark=false \
  --input @source/product.png \
  --save-to generated/product/images \
  --no-open \
  '六段式完整提示词'
```

多张参考图按页面 `references` 的顺序重复 `--input`。纯文生图省略全部 `--input`。成功后只允许移动或改名 `local_path`，不允许裁切、缩放、补边、拼版或脚本叠字。

## 记录与验收边界

生成记录至少保存：`tool=arkcli.+gen`、基础模型完整 ID、实际请求的 `resource_id`（Plan 模型 ID 或 Platform Endpoint ID）、`arkcli_version`、`watermark=false`、`status=succeeded`、生成时间、页面提示词和哈希、方案哈希、来源素材 ID、输出相对路径及 SHA-256、空的 `post_processing`。

Ark CLI 返回成功只证明模型调用成功且文件已落地。图片尺寸、商品身份、文字、构图、商业价值、事实安全和提示词忠实度仍需逐张人工复核。
