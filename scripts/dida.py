#!/usr/bin/env python3
"""Dida365 Open API v1 CLI.

Canonical local entrypoint for the dida365 OpenClaw skill. Endpoint coverage is
kept aligned with https://developer.dida365.com/docs/openapi.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import requests
from config_utils import load_api_config

_CFG: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# HTTP / config
# ---------------------------------------------------------------------------

def get_config() -> dict[str, Any]:
    global _CFG
    if _CFG is None:
        _CFG = load_api_config()
    return _CFG


def get_headers() -> dict[str, str]:
    cfg = get_config()
    return {
        "Authorization": f"Bearer {cfg['access_token']}",
        "Content-Type": "application/json",
    }


def request(method: str, endpoint: str, **kwargs: Any) -> Any:
    cfg = get_config()
    url = f"{cfg['base_url']}{endpoint}"
    try:
        resp = requests.request(method, url, headers=get_headers(), timeout=30, **kwargs)
        if resp.status_code >= 400:
            print(f"❌ API Error [{resp.status_code}]: {resp.text}", file=sys.stderr)
            return None
        if resp.status_code == 204:
            return {}
        return resp.json() if resp.content else {}
    except Exception as e:  # noqa: BLE001 - CLI should show network/config errors plainly
        print(f"❌ Connection Error: {e}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def fix_iso_format(dt_str: str | None) -> str | None:
    """Convert ...+08:00 to Dida's documented ...+0800 form."""
    if not dt_str:
        return dt_str
    if len(dt_str) >= 6 and dt_str[-3] == ":" and dt_str[-6] in "+-":
        return dt_str[:-3] + dt_str[-2:]
    return dt_str


def parse_json_arg(value: str | None, default: Any = None) -> Any:
    if value is None:
        return default
    if value == "-":
        return json.load(sys.stdin)
    p = Path(value)
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return json.loads(value)


def parse_csv(value: str | None) -> list[str] | None:
    if not value:
        return None
    return [x.strip() for x in value.split(",") if x.strip()]


def parse_int_csv(value: str | None) -> list[int] | None:
    if not value:
        return None
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def parse_duration(s: str | None) -> str | None:
    """Simple parser: 30m -> PT30M, 1h -> PT1H, 1d -> P1D."""
    if not s:
        return None
    s = s.lower()
    if s.endswith("m"):
        return f"PT{s[:-1]}M"
    if s.endswith("h"):
        return f"PT{s[:-1]}H"
    if s.endswith("d"):
        return f"P{s[:-1]}D"
    return None


def get_priority(p: str | int | None) -> int | None:
    if p is None or p == "":
        return None
    if isinstance(p, int):
        return p
    low = str(p).lower()
    if low.isdigit():
        return int(low)
    if "high" in low:
        return 5
    if "medium" in low or "med" in low:
        return 3
    if "low" in low:
        return 1
    if "none" in low or "normal" in low:
        return 0
    return int(p)


def get_repeat_rule(r: str | None) -> str | None:
    if not r:
        return None
    low = r.lower()
    if low == "daily":
        return "RRULE:FREQ=DAILY;INTERVAL=1"
    if low == "weekly":
        return "RRULE:FREQ=WEEKLY;INTERVAL=1"
    if low == "monthly":
        return "RRULE:FREQ=MONTHLY;INTERVAL=1"
    if low == "yearly":
        return "RRULE:FREQ=YEARLY;INTERVAL=1"
    if low == "workday":
        return "RRULE:FREQ=WEEKLY;BYDAY=MO,TU,WE,TH,FR;INTERVAL=1"
    return r


def parse_subtasks(s: str | None) -> list[dict[str, Any]] | None:
    if not s:
        return None
    titles = s.replace("\n", ";").split(";")
    return [{"title": t.strip(), "status": 0} for t in titles if t.strip()]


def put_if(payload: dict[str, Any], key: str, value: Any, *, date: bool = False) -> None:
    if value is None:
        return
    payload[key] = fix_iso_format(value) if date else value


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def print_result(data: Any) -> None:
    if data is None:
        raise SystemExit(1)
    print_json(data)


# ---------------------------------------------------------------------------
# Official Task APIs
# ---------------------------------------------------------------------------

def get_task(project_id: str, task_id: str) -> Any:
    """GET /project/{projectId}/task/{taskId}"""
    return request("GET", f"/project/{project_id}/task/{task_id}")


def create_task(
    title: str,
    project_id: str | None = None,
    content: str | None = None,
    desc: str | None = None,
    is_all_day: bool | None = None,
    start_date: str | None = None,
    due_date: str | None = None,
    time_zone: str | None = None,
    reminders: list[Any] | None = None,
    tags: list[str] | None = None,
    repeat_flag: str | None = None,
    priority: int | None = None,
    sort_order: int | None = None,
    items: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> Any:
    """POST /task"""
    payload: dict[str, Any] = dict(extra or {})
    payload["title"] = title
    put_if(payload, "projectId", project_id)
    put_if(payload, "content", content)
    put_if(payload, "desc", desc)
    put_if(payload, "isAllDay", is_all_day)
    put_if(payload, "startDate", start_date, date=True)
    put_if(payload, "dueDate", due_date, date=True)
    put_if(payload, "timeZone", time_zone)
    put_if(payload, "reminders", reminders)
    put_if(payload, "tags", tags)
    put_if(payload, "repeatFlag", repeat_flag)
    put_if(payload, "priority", priority)
    put_if(payload, "sortOrder", sort_order)
    put_if(payload, "items", items)
    return request("POST", "/task", json=payload)


def update_task(task_id: str, project_id: str, extra: dict[str, Any] | None = None, **kwargs: Any) -> Any:
    """POST /task/{taskId}"""
    payload: dict[str, Any] = dict(extra or {})
    payload["id"] = task_id
    payload["projectId"] = project_id
    snake_map = {
        "is_all_day": "isAllDay",
        "start_date": "startDate",
        "due_date": "dueDate",
        "time_zone": "timeZone",
        "repeat_flag": "repeatFlag",
        "sort_order": "sortOrder",
    }
    date_keys = {"startDate", "dueDate"}
    valid_keys = {
        "title", "content", "desc", "isAllDay", "startDate", "dueDate", "timeZone",
        "reminders", "tags", "repeatFlag", "priority", "sortOrder", "items", "status",
    }
    for key, value in kwargs.items():
        if value is None:
            continue
        api_key = snake_map.get(key, key)
        if api_key in valid_keys:
            payload[api_key] = fix_iso_format(value) if api_key in date_keys else value
    return request("POST", f"/task/{task_id}", json=payload)


def complete_task(project_id: str, task_id: str) -> Any:
    """POST /project/{projectId}/task/{taskId}/complete"""
    return request("POST", f"/project/{project_id}/task/{task_id}/complete")


def delete_task(project_id: str, task_id: str) -> Any:
    """DELETE /project/{projectId}/task/{taskId}"""
    return request("DELETE", f"/project/{project_id}/task/{task_id}")


def move_tasks(moves: list[dict[str, str]]) -> Any:
    """POST /task/move"""
    return request("POST", "/task/move", json=moves)


def list_completed_tasks(project_ids: list[str] | None = None, start_date: str | None = None, end_date: str | None = None) -> Any:
    """POST /task/completed"""
    payload: dict[str, Any] = {}
    put_if(payload, "projectIds", project_ids)
    put_if(payload, "startDate", start_date, date=True)
    put_if(payload, "endDate", end_date, date=True)
    return request("POST", "/task/completed", json=payload)


def filter_tasks(
    project_ids: list[str] | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    priority: list[int] | None = None,
    tags: list[str] | None = None,
    status: list[int] | None = None,
    extra: dict[str, Any] | None = None,
) -> Any:
    """POST /task/filter"""
    payload: dict[str, Any] = dict(extra or {})
    put_if(payload, "projectIds", project_ids)
    put_if(payload, "startDate", start_date, date=True)
    put_if(payload, "endDate", end_date, date=True)
    put_if(payload, "priority", priority)
    put_if(payload, "tag", tags)
    put_if(payload, "status", status)
    return request("POST", "/task/filter", json=payload)


# ---------------------------------------------------------------------------
# Official Project APIs
# ---------------------------------------------------------------------------

def get_projects() -> Any:
    """GET /project"""
    return request("GET", "/project") or []


def get_project(project_id: str) -> Any:
    """GET /project/{projectId}"""
    return request("GET", f"/project/{project_id}")


def get_project_with_data(project_id: str) -> Any:
    """GET /project/{projectId}/data"""
    return request("GET", f"/project/{project_id}/data")


def create_project(name: str, color: str | None = None, sort_order: int | None = None, view_mode: str | None = None, kind: str | None = None, extra: dict[str, Any] | None = None) -> Any:
    """POST /project"""
    payload: dict[str, Any] = dict(extra or {})
    payload["name"] = name
    put_if(payload, "color", color)
    put_if(payload, "sortOrder", sort_order)
    put_if(payload, "viewMode", view_mode)
    put_if(payload, "kind", kind)
    return request("POST", "/project", json=payload)


def update_project(project_id: str, name: str | None = None, color: str | None = None, sort_order: int | None = None, view_mode: str | None = None, kind: str | None = None, extra: dict[str, Any] | None = None) -> Any:
    """POST /project/{projectId}"""
    payload: dict[str, Any] = dict(extra or {})
    put_if(payload, "name", name)
    put_if(payload, "color", color)
    put_if(payload, "sortOrder", sort_order)
    put_if(payload, "viewMode", view_mode)
    put_if(payload, "kind", kind)
    return request("POST", f"/project/{project_id}", json=payload)


def delete_project(project_id: str) -> Any:
    """DELETE /project/{projectId}"""
    return request("DELETE", f"/project/{project_id}")


# ---------------------------------------------------------------------------
# Official Focus APIs
# ---------------------------------------------------------------------------

def get_focus(focus_id: str, focus_type: int) -> Any:
    """GET /focus/{focusId}?type={0|1}"""
    return request("GET", f"/focus/{focus_id}", params={"type": focus_type})


def list_focuses(from_time: str, to_time: str, focus_type: int) -> Any:
    """GET /focus?from=...&to=...&type={0|1}"""
    return request("GET", "/focus", params={"from": fix_iso_format(from_time), "to": fix_iso_format(to_time), "type": focus_type})


def delete_focus(focus_id: str, focus_type: int) -> Any:
    """DELETE /focus/{focusId}?type={0|1}"""
    return request("DELETE", f"/focus/{focus_id}", params={"type": focus_type})


# ---------------------------------------------------------------------------
# Official Habit APIs
# ---------------------------------------------------------------------------

def get_habit(habit_id: str) -> Any:
    """GET /habit/{habitId}"""
    return request("GET", f"/habit/{habit_id}")


def list_habits() -> Any:
    """GET /habit"""
    return request("GET", "/habit")


def create_habit(body: dict[str, Any]) -> Any:
    """POST /habit"""
    return request("POST", "/habit", json=body)


def update_habit(habit_id: str, body: dict[str, Any]) -> Any:
    """POST /habit/{habitId}"""
    return request("POST", f"/habit/{habit_id}", json=body)


def checkin_habit(habit_id: str, body: dict[str, Any]) -> Any:
    """POST /habit/{habitId}/checkin"""
    return request("POST", f"/habit/{habit_id}/checkin", json=body)


def get_habit_checkins(habit_ids: list[str], from_stamp: str, to_stamp: str) -> Any:
    """GET /habit/checkins"""
    return request("GET", "/habit/checkins", params={"habitIds": ",".join(habit_ids), "from": from_stamp, "to": to_stamp})


# ---------------------------------------------------------------------------
# Higher-level helpers used by legacy convenience commands
# ---------------------------------------------------------------------------

def get_tasks(project_id: str) -> list[dict[str, Any]]:
    data = get_project_with_data(project_id)
    return data.get("tasks", []) if isinstance(data, dict) else []


def find_task(target: str) -> tuple[dict[str, Any] | None, str | None]:
    projects = get_projects()
    all_projects = [{"id": "inbox", "name": "Inbox"}] + (projects if isinstance(projects, list) else [])
    for project in all_projects:
        project_id = project["id"]
        for task in get_tasks(project_id):
            if task.get("id") == target or target in task.get("title", ""):
                return task, project_id
    return None, None


# ---------------------------------------------------------------------------
# CLI command handlers
# ---------------------------------------------------------------------------

def cmd_legacy_list(args: argparse.Namespace) -> None:
    print("📋 Dida365 Tasks...")
    projects = get_projects()
    targets = [{"id": "inbox", "name": "📥 Inbox"}] + (projects[:5] if isinstance(projects, list) else [])
    if getattr(args, "project", None):
        needle = args.project.lower()
        targets = [p for p in targets if needle in p.get("name", "").lower() or needle == p.get("id", "").lower()]
    for project in targets:
        tasks = get_tasks(project["id"])
        active = [t for t in tasks if t.get("status") == 0]
        if not active:
            continue
        print(f"\n📂 {project.get('name', project['id'])}:")
        for task in active:
            prio = {5: "🔴", 3: "🟡", 1: "🔵", 0: "⚪"}.get(task.get("priority"), "⚪")
            due = (task.get("dueDate") or "")[:10]
            date = f" 📅{due}" if due else ""
            print(f"  {prio} {task.get('title')}{date} (ID: {task.get('id')})")


def build_task_create_from_args(args: argparse.Namespace) -> Any:
    reminders = parse_json_arg(args.reminders, []) or []
    if args.remind:
        reminders.append("TRIGGER:PT0S")
    if args.remind_before:
        dur = parse_duration(args.remind_before)
        if dur:
            reminders.append(f"TRIGGER:-{dur}")
    items = parse_json_arg(args.items, None) or parse_subtasks(args.subtasks)
    return create_task(
        args.title,
        project_id=args.project_id,
        content=args.content,
        desc=args.desc,
        is_all_day=args.is_all_day,
        start_date=args.start_date,
        due_date=args.due_date,
        time_zone=args.time_zone,
        reminders=reminders or None,
        tags=parse_csv(args.tags),
        repeat_flag=get_repeat_rule(args.repeat_flag),
        priority=get_priority(args.priority),
        sort_order=args.sort_order,
        items=items,
        extra=parse_json_arg(args.json, {}),
    )


def cmd_legacy_add(args: argparse.Namespace) -> None:
    args.project_id = None
    if args.project:
        projects = get_projects()
        if isinstance(projects, list):
            match = next((p for p in projects if args.project in p.get("name", "")), None)
            if match:
                args.project_id = match["id"]
    args.due_date = args.due
    args.start_date = None
    args.desc = None
    args.is_all_day = None
    args.time_zone = "Asia/Shanghai" if args.due else None
    args.reminders = None
    args.repeat_flag = args.repeat
    args.tags = None
    args.items = None
    args.json = None
    args.sort_order = None
    data = build_task_create_from_args(args)
    if data is None:
        raise SystemExit(1)
    print(f"✅ Created: {data.get('title', 'Task') if isinstance(data, dict) else 'Task'}")


def cmd_legacy_complete(args: argparse.Namespace) -> None:
    task, project_id = find_task(args.target)
    if not task or not project_id:
        print("❌ Not found.")
        raise SystemExit(1)
    data = complete_task(project_id, task["id"])
    if data is None:
        raise SystemExit(1)
    print(f"✅ Completed: {task.get('title')}")


def add_common_task_fields(p: argparse.ArgumentParser, *, include_title: bool = True, project_id_required: bool = False) -> None:
    if include_title:
        p.add_argument("title")
    p.add_argument("--json", help="JSON object, file path, or '-' for stdin; merged into request body")
    p.add_argument("--project-id", required=project_id_required)
    p.add_argument("--content")
    p.add_argument("--desc")
    p.add_argument("--is-all-day", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--start-date")
    p.add_argument("--due-date", "--due", dest="due_date")
    p.add_argument("--time-zone")
    p.add_argument("--reminders", help="JSON list, file path, or '-' for stdin")
    p.add_argument("--tags", help="Comma-separated tags")
    p.add_argument("--repeat-flag", "--repeat", dest="repeat_flag")
    p.add_argument("--priority")
    p.add_argument("--sort-order", type=int)
    p.add_argument("--items", help="JSON list, file path, or '-' for stdin")
    p.add_argument("--subtasks", help="Semicolon/newline separated subtasks")
    p.add_argument("--remind", action="store_true")
    p.add_argument("--remind-before")


def add_project_fields(p: argparse.ArgumentParser, *, include_name: bool = True) -> None:
    if include_name:
        p.add_argument("name")
    p.add_argument("--json", help="JSON object, file path, or '-' for stdin; merged into request body")
    p.add_argument("--color")
    p.add_argument("--sort-order", type=int)
    p.add_argument("--view-mode", choices=["list", "kanban", "timeline"])
    p.add_argument("--kind", choices=["TASK", "NOTE"])


def add_habit_fields(p: argparse.ArgumentParser, *, include_name: bool = True) -> None:
    if include_name:
        p.add_argument("name", nargs="?")
    p.add_argument("--json", help="JSON object, file path, or '-' for stdin; merged into request body")
    p.add_argument("--icon-res")
    p.add_argument("--color")
    p.add_argument("--sort-order", type=int)
    p.add_argument("--status", type=int)
    p.add_argument("--encouragement")
    p.add_argument("--type")
    p.add_argument("--goal", type=float)
    p.add_argument("--step", type=float)
    p.add_argument("--unit")
    p.add_argument("--repeat-rule")
    p.add_argument("--reminders", help="JSON list, file path, or '-' for stdin")
    p.add_argument("--record-enable", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--section-id")
    p.add_argument("--target-days", type=int)
    p.add_argument("--target-start-date", type=int)
    p.add_argument("--completed-cycles", type=int)
    p.add_argument("--ex-dates", help="Comma-separated excluded dates")
    p.add_argument("--style", type=int)


def habit_body_from_args(args: argparse.Namespace) -> dict[str, Any]:
    body = parse_json_arg(args.json, {}) or {}
    put_if(body, "name", getattr(args, "name", None))
    put_if(body, "iconRes", args.icon_res)
    put_if(body, "color", args.color)
    put_if(body, "sortOrder", args.sort_order)
    put_if(body, "status", args.status)
    put_if(body, "encouragement", args.encouragement)
    put_if(body, "type", args.type)
    put_if(body, "goal", args.goal)
    put_if(body, "step", args.step)
    put_if(body, "unit", args.unit)
    put_if(body, "repeatRule", args.repeat_rule)
    put_if(body, "reminders", parse_json_arg(args.reminders, None))
    put_if(body, "recordEnable", args.record_enable)
    put_if(body, "sectionId", args.section_id)
    put_if(body, "targetDays", args.target_days)
    put_if(body, "targetStartDate", args.target_start_date)
    put_if(body, "completedCycles", args.completed_cycles)
    put_if(body, "exDates", parse_csv(args.ex_dates))
    put_if(body, "style", args.style)
    return body


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dida365 Open API v1 CLI")
    sub = parser.add_subparsers(dest="command")

    # Legacy convenience commands retained for compatibility with older SKILL.md/wrappers.
    legacy_list = sub.add_parser("list", help="Legacy: list active tasks in Inbox + first projects")
    legacy_list.add_argument("--project", help="Filter by project/list name substring or id")
    legacy_list.set_defaults(func=cmd_legacy_list)
    add = sub.add_parser("add", help="Legacy: create a task")
    add.add_argument("title")
    add.add_argument("--content")
    add.add_argument("--priority", default="0")
    add.add_argument("--due")
    add.add_argument("--project")
    add.add_argument("--remind", action="store_true")
    add.add_argument("--remind-before")
    add.add_argument("--repeat")
    add.add_argument("--subtasks")
    add.set_defaults(func=cmd_legacy_add)
    comp = sub.add_parser("complete", help="Legacy: complete by title substring or id")
    comp.add_argument("target")
    comp.set_defaults(func=cmd_legacy_complete)

    # Task group
    task = sub.add_parser("task", help="Official Task APIs")
    task_sub = task.add_subparsers(dest="task_command", required=True)
    p = task_sub.add_parser("get", help="GET /project/{projectId}/task/{taskId}")
    p.add_argument("project_id"); p.add_argument("task_id")
    p.set_defaults(func=lambda a: print_result(get_task(a.project_id, a.task_id)))
    p = task_sub.add_parser("create", help="POST /task")
    add_common_task_fields(p, project_id_required=True)
    p.set_defaults(func=lambda a: print_result(build_task_create_from_args(a)))
    p = task_sub.add_parser("update", help="POST /task/{taskId}")
    p.add_argument("task_id"); add_common_task_fields(p, include_title=False, project_id_required=True)
    p.add_argument("--title")
    p.add_argument("--status", type=int)
    p.set_defaults(func=lambda a: print_result(update_task(
        a.task_id, a.project_id, extra=parse_json_arg(a.json, {}), title=a.title, content=a.content,
        desc=a.desc, is_all_day=a.is_all_day, start_date=a.start_date, due_date=a.due_date,
        time_zone=a.time_zone, reminders=parse_json_arg(a.reminders, None), tags=parse_csv(a.tags),
        repeat_flag=get_repeat_rule(a.repeat_flag), priority=get_priority(a.priority), sort_order=a.sort_order,
        items=parse_json_arg(a.items, None) or parse_subtasks(a.subtasks), status=a.status,
    )))
    p = task_sub.add_parser("complete", help="POST /project/{projectId}/task/{taskId}/complete")
    p.add_argument("project_id"); p.add_argument("task_id")
    p.set_defaults(func=lambda a: print_result(complete_task(a.project_id, a.task_id)))
    p = task_sub.add_parser("delete", help="DELETE /project/{projectId}/task/{taskId}")
    p.add_argument("project_id"); p.add_argument("task_id")
    p.set_defaults(func=lambda a: print_result(delete_task(a.project_id, a.task_id)))
    p = task_sub.add_parser("move", help="POST /task/move")
    p.add_argument("--json", help="JSON array of moves, file path, or '-' for stdin")
    p.add_argument("--from-project-id"); p.add_argument("--to-project-id"); p.add_argument("--task-id")
    p.set_defaults(func=lambda a: print_result(move_tasks(parse_json_arg(a.json, None) or [{"fromProjectId": a.from_project_id, "toProjectId": a.to_project_id, "taskId": a.task_id}])))
    p = task_sub.add_parser("completed", help="POST /task/completed")
    p.add_argument("--project-ids"); p.add_argument("--start-date"); p.add_argument("--end-date")
    p.set_defaults(func=lambda a: print_result(list_completed_tasks(parse_csv(a.project_ids), a.start_date, a.end_date)))
    p = task_sub.add_parser("filter", help="POST /task/filter")
    p.add_argument("--json", help="JSON object, file path, or '-' for stdin")
    p.add_argument("--project-ids"); p.add_argument("--start-date"); p.add_argument("--end-date")
    p.add_argument("--priority", help="Comma-separated priorities, e.g. 0,1,3,5")
    p.add_argument("--tags", help="Comma-separated tags")
    p.add_argument("--status", help="Comma-separated statuses")
    p.set_defaults(func=lambda a: print_result(filter_tasks(parse_csv(a.project_ids), a.start_date, a.end_date, parse_int_csv(a.priority), parse_csv(a.tags), parse_int_csv(a.status), parse_json_arg(a.json, {}))))

    # Project group
    project = sub.add_parser("project", help="Official Project APIs")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    project_sub.add_parser("list", help="GET /project").set_defaults(func=lambda a: print_result(get_projects()))
    p = project_sub.add_parser("get", help="GET /project/{projectId}")
    p.add_argument("project_id"); p.set_defaults(func=lambda a: print_result(get_project(a.project_id)))
    p = project_sub.add_parser("data", help="GET /project/{projectId}/data")
    p.add_argument("project_id"); p.set_defaults(func=lambda a: print_result(get_project_with_data(a.project_id)))
    p = project_sub.add_parser("create", help="POST /project")
    add_project_fields(p)
    p.set_defaults(func=lambda a: print_result(create_project(a.name, a.color, a.sort_order, a.view_mode, a.kind, parse_json_arg(a.json, {}))))
    p = project_sub.add_parser("update", help="POST /project/{projectId}")
    p.add_argument("project_id"); add_project_fields(p, include_name=False); p.add_argument("--name")
    p.set_defaults(func=lambda a: print_result(update_project(a.project_id, a.name, a.color, a.sort_order, a.view_mode, a.kind, parse_json_arg(a.json, {}))))
    p = project_sub.add_parser("delete", help="DELETE /project/{projectId}")
    p.add_argument("project_id"); p.set_defaults(func=lambda a: print_result(delete_project(a.project_id)))

    # Focus group
    focus = sub.add_parser("focus", help="Official Focus APIs")
    focus_sub = focus.add_subparsers(dest="focus_command", required=True)
    p = focus_sub.add_parser("get", help="GET /focus/{focusId}")
    p.add_argument("focus_id"); p.add_argument("--type", required=True, type=int, choices=[0, 1])
    p.set_defaults(func=lambda a: print_result(get_focus(a.focus_id, a.type)))
    p = focus_sub.add_parser("list", help="GET /focus")
    p.add_argument("--from", dest="from_time", required=True); p.add_argument("--to", dest="to_time", required=True)
    p.add_argument("--type", required=True, type=int, choices=[0, 1])
    p.set_defaults(func=lambda a: print_result(list_focuses(a.from_time, a.to_time, a.type)))
    p = focus_sub.add_parser("delete", help="DELETE /focus/{focusId}")
    p.add_argument("focus_id"); p.add_argument("--type", required=True, type=int, choices=[0, 1])
    p.set_defaults(func=lambda a: print_result(delete_focus(a.focus_id, a.type)))

    # Habit group
    habit = sub.add_parser("habit", help="Official Habit APIs")
    habit_sub = habit.add_subparsers(dest="habit_command", required=True)
    habit_sub.add_parser("list", help="GET /habit").set_defaults(func=lambda a: print_result(list_habits()))
    p = habit_sub.add_parser("get", help="GET /habit/{habitId}")
    p.add_argument("habit_id"); p.set_defaults(func=lambda a: print_result(get_habit(a.habit_id)))
    p = habit_sub.add_parser("create", help="POST /habit")
    add_habit_fields(p)
    p.set_defaults(func=lambda a: print_result(create_habit(habit_body_from_args(a))))
    p = habit_sub.add_parser("update", help="POST /habit/{habitId}")
    p.add_argument("habit_id"); add_habit_fields(p, include_name=False); p.add_argument("--name")
    p.set_defaults(func=lambda a: print_result(update_habit(a.habit_id, habit_body_from_args(a))))
    p = habit_sub.add_parser("checkin", help="POST /habit/{habitId}/checkin")
    p.add_argument("habit_id")
    p.add_argument("--json", help="JSON object, file path, or '-' for stdin; merged into request body")
    p.add_argument("--stamp", type=int, help="YYYYMMDD, required unless provided by --json")
    p.add_argument("--time")
    p.add_argument("--op-time")
    p.add_argument("--value", type=float)
    p.add_argument("--goal", type=float)
    p.add_argument("--status", type=int)
    def _habit_checkin_cmd(a):
        body = parse_json_arg(a.json, {}) or {}
        put_if(body, "stamp", a.stamp)
        put_if(body, "time", a.time, date=True)
        put_if(body, "opTime", a.op_time, date=True)
        put_if(body, "value", a.value)
        put_if(body, "goal", a.goal)
        put_if(body, "status", a.status)
        return print_result(checkin_habit(a.habit_id, body))
    p.set_defaults(func=_habit_checkin_cmd)
    p = habit_sub.add_parser("checkins", help="GET /habit/checkins")
    p.add_argument("--habit-ids", required=True); p.add_argument("--from", dest="from_stamp", required=True); p.add_argument("--to", dest="to_stamp", required=True)
    p.set_defaults(func=lambda a: print_result(get_habit_checkins(parse_csv(a.habit_ids) or [], a.from_stamp, a.to_stamp)))

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
