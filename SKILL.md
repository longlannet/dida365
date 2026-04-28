---
name: dida365
description: Complete official Open API v1 integration for Dida365 (TickTick China). Covers every documented Task, Project, Focus, and Habit endpoint: create/list/get/update/delete/complete/move/filter tasks, projects, focus records, habits, and habit check-ins. Use when the user mentions Dida365, 滴答清单, TickTick China, tasks, todos, reminders, projects/lists, focus/pomodoro, or habits.
homepage: https://github.com/longlannet/dida365
metadata:
  openclaw:
    emoji: "✅"
    requires:
      bins: [python3]
    install:
      - id: dida365-python
        kind: shell
        script: scripts/install.sh
        label: Install dida365 skill
---

# Dida365 Skill

Use this skill to manage tasks, projects, focus, and habits through the official Dida365 Open API v1.

## When to use

Use this skill when the user wants:
- Add/list/complete/update tasks or todos in Dida365
- Query or manage projects/lists in Dida365
- Check or delete focus/pomodoro records
- Create/update/check-in habits in Dida365
- Any Dida365/TickTick China automation that involves official Open API operations

## Quick start

```bash
bash scripts/install.sh
bash scripts/check.sh
python3 scripts/dida.py --help
```

`install.sh` 默认使用系统 `python3`；如果缺 `requests`，会直接给当前 Python 环境补装 `requirements.txt`，不自动创建 `.venv`。

## Auth

If `config/token.json` is missing or expired:

```bash
cd ~/.openclaw/workspace/skills/dida365
python3 scripts/get_auth_url.py
# open URL, login, copy code from redirect URL
python3 scripts/exchange_token.py '<code>'
```

OAuth config sources, in priority order:
- `DIDA_CLIENT_ID`, `DIDA_CLIENT_SECRET`, optional `DIDA_REDIRECT_URI`
- `config/oauth.json` with `client_id`, `client_secret`, optional `redirect_uri`
- optional `config/.env` with the same environment variable names

Runtime API token sources:
- `DIDA_ACCESS_TOKEN` + optional `DIDA_BASE_URL`
- `config/token.json` with `access_token` and optional `base_url`

Default API base: `https://api.dida365.com/open/v1`

## Security rules

- Never print or expose `config/token.json`, `config/.env`, or `config/oauth.json`.
- Local secret/config files should be mode `600`; `config/` should be `700`.
- OAuth client credentials belong in environment variables or `config/oauth.json`, never hard-coded in scripts.
- For destructive/write operations, confirm user intent unless the user clearly requested the action.

## Full official endpoint coverage

### Task

```bash
python3 scripts/dida.py task get <project_id> <task_id>
python3 scripts/dida.py task create "Title" --project-id <project_id> [fields]
python3 scripts/dida.py task update <task_id> --project-id <project_id> [fields]
python3 scripts/dida.py task complete <project_id> <task_id>
python3 scripts/dida.py task delete <project_id> <task_id>
python3 scripts/dida.py task move --from-project-id <from> --to-project-id <to> --task-id <task>
python3 scripts/dida.py task completed --project-ids <id1,id2> --start-date <ISO> --end-date <ISO>
python3 scripts/dida.py task filter --project-ids <id1,id2> --priority 0,1,3,5 --tags tag1,tag2 --status 0,2
```

Task create/update fields include:
`--content`, `--desc`, `--is-all-day/--no-is-all-day`, `--start-date`, `--due-date/--due`, `--time-zone`, `--reminders <json>`, `--tags a,b`, `--repeat-flag/--repeat`, `--priority`, `--sort-order`, `--items <json>`, `--subtasks 'one;two'`, `--json <object|file|->`.

Legacy convenience aliases still work:

```bash
python3 scripts/dida.py list
python3 scripts/dida.py add "Buy Milk" --due "2026-04-28T18:00:00+08:00" --priority high
python3 scripts/dida.py complete "Buy Milk"
python3 scripts/add_task.py "Buy Milk" --content "2 bottles"
python3 scripts/list_tasks.py
```

### Project

```bash
python3 scripts/dida.py project list
python3 scripts/dida.py project get <project_id>
python3 scripts/dida.py project data <project_id>
python3 scripts/dida.py project create "Project Name" --color '#F18181' --view-mode list --kind TASK
python3 scripts/dida.py project update <project_id> --name "New Name"
python3 scripts/dida.py project delete <project_id>
```

Project create/update accepts `--json <object|file|->` for any documented body fields.

### Focus

```bash
python3 scripts/dida.py focus get <focus_id> --type 0      # 0 Pomodoro, 1 Timing
python3 scripts/dida.py focus list --from <ISO> --to <ISO> --type 1
python3 scripts/dida.py focus delete <focus_id> --type 0
```

### Habit

```bash
python3 scripts/dida.py habit list
python3 scripts/dida.py habit get <habit_id>
python3 scripts/dida.py habit create "Read" --repeat-rule 'RRULE:FREQ=DAILY;INTERVAL=1' --goal 1 --unit times
python3 scripts/dida.py habit update <habit_id> --name "Read daily"
python3 scripts/dida.py habit checkin <habit_id> --stamp 20260428 --value 1 --goal 1
python3 scripts/dida.py habit checkins --habit-ids habit-1,habit-2 --from 20260401 --to 20260407
```

Habit create/update fields include:
`--name` for update, plus `--icon-res`, `--color`, `--sort-order`, `--status`, `--encouragement`, `--type`, `--goal`, `--step`, `--unit`, `--repeat-rule`, `--reminders <json>`, `--record-enable/--no-record-enable`, `--section-id`, `--target-days`, `--target-start-date`, `--completed-cycles`, `--ex-dates a,b`, `--style`, `--json <object|file|->`.

Habit check-in fields include:
`--stamp`, `--time`, `--op-time`, `--value`, `--goal`, `--status`, plus `--json <object|file|->`.

## JSON escape hatch

Every complex request body supports `--json` with:
- inline JSON object/list
- file path
- `-` for stdin

Use `--json` when the official docs add a field before the CLI grows a named flag.

## Notes

- Run commands from the skill root so local config is used.
- Re-run `scripts/install.sh` if setup is missing or stale.
- Keep detailed human-facing usage in `README.md`.
