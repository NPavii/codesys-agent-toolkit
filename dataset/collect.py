#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""collect.py - сборщик решений для Library/_dataset (см. README.md датасета).

Почему так: bridge_daemon удаляет task-файл после исполнения, а bridge_client
удаляет result-файл после чтения (bridge_client.py:93) - ретроспективно собрать
нечего. Поэтому сбор встраивается в точку отправки задачи.

Режимы:
  submit <task.json> [--timeout N]   отправить задачу мосту через bridge_client,
                                     заархивировать task+result парой, добавить
                                     сводку в bridge_log/index.jsonl
  scan                               заархивировать "осиротевшие" *.result.json
                                     в queue (клиент не дочитал / упал)
  digest                             сводка архива (операции, вердикты сборок)

Архив: Library/_dataset/bridge_log/YYYY-MM/<task_id>.task.json / .result.json
Идемпотентен: уже заархивированные id пропускает.
Демон CODESYS не трогает; только файлы queue/ и собственный архив.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

BRIDGE_DIR = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "CodeSYS-MCP", "bridge"))
QUEUE_DIR = os.path.join(BRIDGE_DIR, "queue")
CLIENT = os.path.join(BRIDGE_DIR, "bridge_client.py")
DATASET_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_ROOT = os.path.join(DATASET_DIR, "bridge_log")
INDEX = os.path.join(LOG_ROOT, "index.jsonl")


def _ym(ts):
    return datetime.fromtimestamp(ts).strftime("%Y-%m")


def _month_dir(ts):
    d = os.path.join(LOG_ROOT, _ym(ts))
    if not os.path.isdir(d):
        os.makedirs(d)
    return d


def _load_index_ids():
    ids = set()
    if os.path.isfile(INDEX):
        with open(INDEX, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ids.add(json.loads(line).get("task_id"))
                except ValueError:
                    pass
    return ids


def _summarize(task_id, task, result):
    """Извлечь из пары task+result компактную сводку для index.jsonl."""
    ops = []
    ok_all = bool(result.get("ok"))
    build = None
    for step in (result.get("data") or {}).get("results") or []:
        op = step.get("op")
        ops.append({"op": op, "ok": bool(step.get("ok"))})
        d = step.get("data") or {}
        if op in ("build", "validate_library"):
            build = {
                "op": op,
                "build_result": d.get("build_result"),
                "warnings": d.get("warnings"),
                "error_count": d.get("error_count"),
            }
    rec = {
        "task_id": task_id,
        "ts": datetime.now().isoformat(timespec="seconds"),
        "op": task.get("op"),
        "ok": ok_all,
        "elapsed_s": result.get("elapsed_s"),
        "ops": ops,
        "build": build,
        "project": (task.get("args") or {}).get("project"),
        "path": (task.get("args") or {}).get("path"),
        "note": None,          # заполняет агент при промоушене в records/
        "record_id": None,     # ссылка на запись в records/YYYY-MM.jsonl
    }
    return rec


def _append_index(rec):
    with open(INDEX, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _archive_pair(task_id, task, result, ts):
    d = _month_dir(ts)
    with open(os.path.join(d, task_id + ".task.json"), "w", encoding="utf-8") as f:
        json.dump(task, f, ensure_ascii=False, indent=1)
    with open(os.path.join(d, task_id + ".result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)


def cmd_submit(task_file, timeout):
    with open(task_file, "r", encoding="utf-8") as f:
        task = json.load(f)
    task_id = "t%d-%d" % (int(time.time() * 1000), os.getpid())
    # bridge_client сам копирует task в queue и ждёт result; result он удалит -
    # поэтому дублируем task в архив ДО отправки, result восстановим из stdout.
    r = subprocess.run(
        [sys.executable, CLIENT, "submit", task_file, "--timeout", str(timeout)],
        capture_output=True, text=True, cwd=BRIDGE_DIR)
    ts = time.time()
    try:
        result = json.loads(r.stdout)
    except ValueError:
        print("collect: result is not JSON (bridge output below); nothing archived",
              file=sys.stderr)
        sys.stdout.write(r.stdout)
        sys.stderr.write(r.stderr)
        return r.returncode or 1
    _archive_pair(task_id, task, result, ts)
    rec = _summarize(task_id, task, result)
    _append_index(rec)
    print(json.dumps(rec, ensure_ascii=False, indent=1))
    return 0 if result.get("ok") else 1


def cmd_scan():
    """Забрать осиротевшие result-файлы из queue (task-файлы уже удалены)."""
    archived = 0
    known = _load_index_ids()
    for name in sorted(os.listdir(QUEUE_DIR)):
        if not name.endswith(".result.json"):
            continue
        task_id = name[:-len(".result.json")]
        if task_id in known:
            continue
        with open(os.path.join(QUEUE_DIR, name), "r", encoding="utf-8") as f:
            try:
                result = json.load(f)
            except ValueError:
                continue
        task = {"op": None, "args": {}, "_recovered": True}
        ts = os.path.getmtime(os.path.join(QUEUE_DIR, name))
        _archive_pair(task_id, task, result, ts)
        rec = _summarize(task_id, task, result)
        rec["_recovered"] = True
        _append_index(rec)
        os.remove(os.path.join(QUEUE_DIR, name))
        archived += 1
    print("scan: archived %d orphan result(s)" % archived)
    return 0


def cmd_digest():
    if not os.path.isfile(INDEX):
        print("digest: index empty")
        return 0
    n = 0
    ok = 0
    builds = []
    ops_stat = {}
    with open(INDEX, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            n += 1
            ok += 1 if rec.get("ok") else 0
            if rec.get("build"):
                builds.append(rec["build"])
            o = rec.get("op")
            ops_stat[o] = ops_stat.get(o, 0) + 1
    print("digest: %d task(s), ok %d, fail %d" % (n, ok, n - ok))
    for k in sorted(ops_stat, key=lambda x: -ops_stat[x]):
        print("  %-20s %d" % (k, ops_stat[k]))
    for b in builds[-10:]:
        print("  build:", json.dumps(b, ensure_ascii=False))
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    mode = argv[1]
    if mode == "submit":
        if len(argv) < 3:
            print("usage: collect.py submit <task.json> [--timeout N]", file=sys.stderr)
            return 2
        timeout = 240
        if "--timeout" in argv:
            i = argv.index("--timeout")
            timeout = int(argv[i + 1])
        return cmd_submit(argv[2], timeout)
    if mode == "scan":
        return cmd_scan()
    if mode == "digest":
        return cmd_digest()
    print("unknown mode: %s" % mode, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
