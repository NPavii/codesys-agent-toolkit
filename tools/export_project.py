# -*- coding: utf-8 -*-
# Export the full code of a CODESYS project (.project) to text files.
#
# Walks the object tree via the warm bridge daemon (op dump_tree) and writes
# every object's declaration + implementation as .txt, mirroring the project's
# folder structure on disk.
#
# Usage:
#   python Tools/export_project.py [--project Project/<My>/<my>.project]
#                                  [--out Project/<My>/Export_<timestamp>]
#                                  [--path ""]            # root object path inside project
#                                  [--timeout 300]
#
# Output:
#   <out>/<ObjectPath>/<Object>.txt   - code of every object (header + DECLARATION + IMPLEMENTATION)
#   <out>/_index.txt                  - manifest: relative path | type | guid
#   <out>/_dump_tree.json             - raw bridge response (source of truth for re-runs)
import argparse
import io
import json
import os
import re
import subprocess
import sys
import time

WS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRIDGE = os.path.join(WS, "CodeSYS-MCP", "bridge")
CLIENT = os.path.join(BRIDGE, "bridge_client.py")
DAEMON_CMD = os.path.join(BRIDGE, "bridge_daemon.cmd")

DEFAULT_PROJECT = os.path.join(WS, "Project", "Mhw2.5", "mhw2.7.project")

ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def sanitize(name):
    name = ILLEGAL.sub("_", name).strip().strip(".")
    return name or "_"


def ensure_daemon(timeout=180):
    """Start the warm daemon if it is not answering, then wait for it."""
    r = subprocess.run([sys.executable, CLIENT, "ping"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        return True
    print("daemon not responding - starting ...", flush=True)
    subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Start-Process -FilePath '%s' -WindowStyle Minimized" % DAEMON_CMD],
        check=True)
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = subprocess.run([sys.executable, CLIENT, "ping"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            return True
        time.sleep(1.0)
    return False


def submit(task, timeout):
    # NOTE: the task file MUST live outside bridge/queue/ - the daemon treats
    # any *.json in the queue dir as a task and deletes it after processing.
    fd, task_file = __import__("tempfile").mkstemp(
        suffix=".json", prefix="export_")
    os.close(fd)
    try:
        with io.open(task_file, "w", encoding="utf-8") as f:
            json.dump(task, f, ensure_ascii=False)
        deadline = time.time() + timeout
        while True:
            r = subprocess.run(
                [sys.executable, CLIENT, "submit", task_file,
                 "--timeout", str(min(90, max(10, int(deadline - time.time()))))],
                capture_output=True, text=True)
            # a valid ok:true JSON on stdout is accepted even when the client
            # exits non-zero: bridge_client can crash on result-file cleanup
            # (PermissionError) or refuse on a momentarily stale daemon ping
            try:
                data = json.loads(r.stdout, strict=False)
                if data.get("ok") and not data.get("_nuclear_fallback"):
                    return data
            except Exception:
                pass
            if time.time() < deadline and ("not running" in r.stderr or
                                           "timeout" in r.stderr):
                time.sleep(3.0)
                continue
            sys.stderr.write(r.stdout + r.stderr)
            raise RuntimeError("bridge submit failed (rc=%s)" % r.returncode)
    finally:
        try:
            os.remove(task_file)
        except OSError:
            pass


def write_object(out_dir, node, rel_parts, index):
    name = node.get("name", "<unnamed>")
    otype = node.get("type", "?")
    guid = node.get("guid", "")
    decl = node.get("declaration")
    impl = node.get("implementation")
    has_code = decl is not None or impl is not None
    index.append(("%s/%s" % ("/".join(rel_parts), name) if rel_parts else name,
                  otype, guid, "code" if has_code else "info"))

    header = (
        "' ============================================================================\n"
        "' Object : %s\n"
        "' Type   : %s\n"
        "' GUID   : %s\n"
        "' ============================================================================\n"
        % (name, otype, guid))

    if not has_code:
        # no textual code: keep a small info card so the folder layout is complete
        info = header + "\n(no textual declaration/implementation)\n"
        if node.get("dump_error"):
            info += "\n// dump_error: %s\n" % node["dump_error"]
        target = os.path.join(out_dir, sanitize(name) + ".txt")
        with io.open(target, "w", encoding="utf-8") as f:
            f.write(info)
        return

    parts = [header]
    if decl is not None:
        parts.append("\n// ----- DECLARATION -----\n\n" + decl.rstrip() + "\n")
    if node.get("declaration_error"):
        parts.append("\n// declaration_error: %s\n" % node["declaration_error"])
    if impl is not None:
        parts.append("\n// ----- IMPLEMENTATION -----\n\n" + impl.rstrip() + "\n")
    if node.get("implementation_error"):
        parts.append("\n// implementation_error: %s\n" % node["implementation_error"])

    target = os.path.join(out_dir, sanitize(name) + ".txt")
    with io.open(target, "w", encoding="utf-8") as f:
        f.write("".join(parts))


def walk(node, out_dir, rel_parts, index):
    """Recurse over dump_tree nodes. A node may carry BOTH code and children
    (e.g. Device, Application), so children are always recursed into; a
    directory is created only when the node actually has children."""
    for child in node.get("children", []):
        name = child.get("name", "<unnamed>")
        sname = sanitize(name)
        child_rel = rel_parts + [sname]
        has_code = (child.get("declaration") is not None or
                    child.get("implementation") is not None)
        grandkids = child.get("children", [])
        if grandkids:
            sub = os.path.join(out_dir, sname)
            if not os.path.isdir(sub):
                os.makedirs(sub)
            if has_code:
                write_object(out_dir, child, rel_parts, index)
            else:
                index.append(("/".join(child_rel), child.get("type", "?"),
                              child.get("guid", ""), "folder"))
            walk(child, sub, child_rel, index)
        else:
            write_object(out_dir, child, rel_parts, index)


def main():
    ap = argparse.ArgumentParser(description="Export CODESYS project code to txt files.")
    ap.add_argument("--project", default=DEFAULT_PROJECT,
                    help="path to .project file (default: %(default)s)")
    ap.add_argument("--out", default=None,
                    help="output directory (default: <project dir>/Export_<timestamp>)")
    ap.add_argument("--path", default="",
                    help="root object path inside the project (default: project root)")
    ap.add_argument("--timeout", type=int, default=300,
                    help="overall wait budget (seconds)")
    ap.add_argument("--task-timeout", type=int, default=90,
                    help="per-task timeout passed to bridge client (seconds)")
    args = ap.parse_args()

    project = os.path.abspath(args.project)
    if not os.path.isfile(project):
        sys.exit("project not found: %s" % project)
    if args.out:
        out = os.path.abspath(args.out)
    else:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        out = os.path.join(os.path.dirname(project), "Export_" + stamp)
    if not os.path.isdir(out):
        os.makedirs(out)

    if not ensure_daemon():
        sys.exit("daemon did not start within timeout")

    dumped = {"n": 0}

    def try_dump(path):
        try:
            r = submit({"op": "dump_tree",
                        "args": {"project": project, "path": path}},
                       timeout=args.task_timeout)
        except Exception as e:
            return None, "submit: %s" % e
        if r.get("ok"):
            return r["data"]["root"], None
        return None, json.dumps(r, ensure_ascii=False)[:300]

    def list_children(path):
        try:
            r = submit({"op": "list_objects",
                        "args": {"project": project, "path": path,
                                 "recursive": False, "slim": True}},
                       timeout=args.task_timeout)
        except Exception as e:
            return None, "submit: %s" % e
        if not r.get("ok"):
            return None, json.dumps(r, ensure_ascii=False)[:300]
        return [o["name"] for o in r["data"]["objects"]], None

    def dump_adaptive(path, name_hint):
        """dump_tree(path); on failure descend one level and dump each child."""
        node, err = try_dump(path)
        if node is not None:
            dumped["n"] += 1
            if dumped["n"] % 10 == 0:
                print("    ... %d subtrees dumped" % dumped["n"], flush=True)
            return node
        kids, lerr = list_children(path)
        if kids is None or not kids:
            # leaf we cannot read: keep an info card with the error
            return {"name": name_hint, "type": "?", "guid": "",
                    "is_folder": False,
                    "dump_error": (err or lerr or "unknown")[:500]}
        children = [dump_adaptive(path + "/" + k, k) for k in kids]
        return {"name": name_hint, "type": "<folder>", "guid": "",
                "is_folder": True, "children": children}

    print("dump: %s (path=%r) ..." % (project, args.path), flush=True)
    t0 = time.time()
    if args.path:
        roots = [dump_adaptive(args.path, args.path.split("/")[-1])]
    else:
        # whole project: dump_tree crashes on the ScriptProject root (no .type),
        # so start from the top-level objects; big subtrees (Device/...) fall
        # back to child-by-child descent automatically
        kids, err = list_children("")
        if kids is None:
            sys.exit("list_objects failed: %s" % err)
        print("top-level objects: %s" % ", ".join(kids), flush=True)
        roots = []
        for i, name in enumerate(kids):
            print("  [%d/%d] %s" % (i + 1, len(kids), name), flush=True)
            roots.append(dump_adaptive(name, name))

    proj_name = os.path.splitext(os.path.basename(project))[0]
    root = {"name": proj_name, "type": "ScriptProject", "is_folder": True,
            "children": roots}

    with io.open(os.path.join(out, "_dump_tree.json"), "w", encoding="utf-8") as f:
        json.dump(root, f, ensure_ascii=False, indent=1)
    print("dump took %.1f s (%d dump_tree calls)" % (time.time() - t0, dumped["n"]),
          flush=True)

    index = []
    root_name = sanitize(root.get("name") or os.path.splitext(os.path.basename(project))[0])
    root_dir = os.path.join(out, root_name)
    if not os.path.isdir(root_dir):
        os.makedirs(root_dir)
    # the root node itself is a code object (project root has none, usually)
    if root.get("declaration") is not None or root.get("implementation") is not None:
        write_object(root_dir, root, [], index)
    walk(root, root_dir, [root_name], index)

    lines = ["%-70s | %-12s | %s" % ("OBJECT", "TYPE", "GUID"),
             "-" * 110]
    for path, otype, guid, kind in index:
        lines.append("%-70s | %-12s | %s" % (path, otype, guid))
    with io.open(os.path.join(out, "_index.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    n_code = sum(1 for _, _, _, k in index if k == "code")
    print("done: %d objects (%d with code) -> %s" % (len(index), n_code, out))


if __name__ == "__main__":
    main()
