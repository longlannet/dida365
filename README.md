# Dida365

面向 OpenClaw 的 Dida365（滴答清单）官方 Open API v1 CLI。支持任务、清单、专注、习惯四大模块的完整读写操作。

## 它能做什么

- 创建/查询/更新/删除任务，支持子任务、提醒、重复、标签、优先级
- 管理清单/项目（创建、更新、删除、查看数据）
- 查询专注记录（番茄钟/正向计时）
- 创建/更新/打卡习惯，查询习惯打卡记录
- 提供 `--json` 逃生口，兼容官方未来新增字段

## 安装

```bash
bash scripts/install.sh
```

默认使用系统 `python3`；如果缺 `requests`，会直接给当前 Python 环境补装 `requirements.txt`，不自动创建 `.venv`。

## 校验

```bash
bash scripts/check.sh
```

## Auth

创建 `config/oauth.json`（或设置环境变量 `DIDA_CLIENT_ID` / `DIDA_CLIENT_SECRET`），然后：

```bash
python3 scripts/get_auth_url.py
python3 scripts/exchange_token.py '<code>'
```

这会写入 `config/token.json`。示例配置见 `config/oauth.json.example` 和 `config/token.json.example`。

## 常用命令

```bash
# 任务
python3 scripts/dida.py task create "Buy Milk" --project-id <pid> --due "2026-04-28T18:00:00+08:00"
python3 scripts/dida.py task filter --status 0 --priority 5
python3 scripts/dida.py list

# 项目
python3 scripts/dida.py project list
python3 scripts/dida.py project create "New List" --color '#F18181'

# 专注
python3 scripts/dida.py focus list --from "2026-04-01T00:00:00+0800" --to "2026-04-02T00:00:00+0800" --type 1

# 习惯
python3 scripts/dida.py habit list
python3 scripts/dida.py habit checkin <hid> --stamp 20260428 --value 1
```

## 说明

- 请在 skill 根目录运行命令，确保本地 `config/` 生效。
- 如果环境缺失或状态异常，重新运行 `scripts/install.sh`。
- 官方文档：`https://developer.dida365.com/docs/openapi.md`
