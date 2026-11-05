# -*- coding: utf-8 -*-
"""c4_build.py — headless-работа с CODESYS 4 через c4-cli.

Главный инструмент: `c4-cli bootapp compile <Application.iecapp> [target]`
— полноценная офлайн-сборка приложения БЕЗ запуска GUI/сессии:
exit code 0 = успех, иначе ошибки с позициями в stdout (локализован).

Зачем так: JSON-RPC/WS-интерфейс C4 (c4_api.py) тоже работает, но
компилятор по RPC не инвалидирует свой кэш LM от внешних правок файлов,
а bootapp compile всегда собирает с диска. Поэтому рабочий цикл:
    1) правим текстовые файлы проекта (*.prg.st, *.gvl, Libraries.json) напрямую;
    2) c4_build.compile(app) -> (ok, diagnostics);
    3) диагностику показываем/разбираем.

Пример:
    from c4_build import compile_app, C4Project
    ok, diags = compile_app(r"C:\\path\\to\\project.fbsdev")
    for d in diags:
        print(d.severity, d.path, d.line, d.message)

Путь к c4-cli.exe берётся из env C4_CLI (иначе ищется в PATH).
"""
import os
import re
import subprocess
import sys
import tempfile

_C4_CLI = os.environ.get("C4_CLI", "c4-cli")

# строка с позицией: <путь> (<line>, <col>, length: <n>)
_RE_POS = re.compile(r"^(?P<path>.+?)\s*\((?P<line>\d+),\s*(?P<col>\d+)(?:,\s*length:\s*(?P<len>\d+))?\)\s*$")
# строка-итог: «... 3 ошибки, 0 предупреждений ...» / english fallback
_RE_SUM = re.compile(r"(?P<errors>\d+)\s*(?:ошиб|error)", re.I)
_RE_SUMW = re.compile(r"(?P<warns>\d+)\s*(?:предупрежд|warning)", re.I)


class Diag:
    """Одна строка диагностики компилятора."""
    def __init__(self, severity, message, path=None, line=None, col=None, length=None):
        self.severity = severity      # 'Error' | 'Warning' | 'Info'
        self.message = message
        self.path = path
        self.line = line
        self.col = col
        self.length = length

    def __repr__(self):
        loc = f"{self.path}:{self.line}:{self.col}" if self.path else "-"
        return f"<{self.severity} {loc} {self.message[:80]}>"


def _app_of(project_dir):
    """Находит Application.iecapp в проекте (папка .fbsdev)."""
    p = os.path.abspath(project_dir)
    if p.lower().endswith(".iecapp"):
        return p
    candidate = os.path.join(p, "Application.iecapp")
    if os.path.exists(candidate) or os.path.exists(candidate + "^"):
        return candidate
    raise FileNotFoundError(f"Application.iecapp не найден в {p}")


def parse_diagnostics(output):
    """Разбирает stdout c4-cli в список Diag. Работает с любым языком вывода.

    Вывод c4-cli переносит длинные пути по строкам, поэтому строку с позицией
    склеиваем с предыдущими, пока кусок не станет существующим файлом."""
    diags = []
    lines = [l.strip() for l in output.replace("\r", "").split("\n")]
    pending = None   # текст сообщения, ждущий строку с позицией
    for i, ln in enumerate(lines):
        if not ln:
            continue
        m = _RE_POS.match(ln)
        if m:
            tail = m.group("path")
            # c4-cli рвёт длинные пути: склеиваем с хвостами предыдущих строк
            parts = [tail]
            for j in (i - 1, i - 2):
                if j < 0:
                    break
                cand = "".join(reversed(parts))
                if os.path.exists(cand):
                    break
                prev = lines[j]
                # хвост пути не похож на текст сообщения (слова через пробел)
                if re.search(r"[a-zа-яё]\s+[a-zа-яё]", prev, re.I) and not prev.endswith(("^", "\\", "/")):
                    break
                parts.append(prev)
            path = "".join(reversed(parts))
            if not os.path.exists(path):
                path = tail  # не склеилось — оставляем как есть
            if pending:
                diags.append(Diag("Error", pending, path,
                                  int(m.group("line")), int(m.group("col")),
                                  int(m.group("len") or 0)))
                pending = None
            continue
        low = ln.lower()
        if ("error" in low or "ошиб" in low) and not ln.startswith(("info", "warn")):
            # строка вида «Объявите 'x' ...» — потенциально сообщение об ошибке
            if any(k in low for k in ("error", "ошиб", "undeclared", "объявите",
                                      "cannot", "не может", "expected", "ожидал")):
                pending = ln
                continue
        if low.startswith(("warning", "предупрежд")) or " warning" in low:
            diags.append(Diag("Warning", ln))
        elif low.startswith("info:"):
            pass
    # строки-«хвосты»: сообщение с позицией не пришло — оставляем без позиции
    if pending:
        diags.append(Diag("Error", pending))
    return diags


def compile_app(project_or_app, target_dir=None, timeout=300, verbose=False):
    """Собирает приложение headless.

    project_or_app — папка проекта (*.fbsdev) или путь к Application.iecapp.
    target_dir     — куда положить результат (по умолчанию временная папка,
                     чтобы не писать в проект; .bootapp/ внутри проекта — стандарт).
    Возвращает (ok, [Diag...], raw_output).
    ok = exit code 0 и сводка без ошибок.
    """
    app = _app_of(project_or_app)
    if target_dir is None:
        target_dir = tempfile.mkdtemp(prefix="c4boot_")
    os.makedirs(target_dir, exist_ok=True)
    cmd = [_C4_CLI, "bootapp", "compile", app, target_dir]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout)
    out = proc.stdout + "\n" + proc.stderr
    if verbose:
        sys.stdout.write(out)
    diags = parse_diagnostics(out)
    ok = proc.returncode == 0 and not any(d.severity == "Error" for d in diags)
    return ok, diags, out


class C4Project:
    """Удобная обёртка над папкой проекта C4."""

    def __init__(self, project_dir):
        self.dir = os.path.abspath(project_dir)
        self.name = os.path.basename(self.dir.rstrip("/\\"))
        if not self.name.endswith(".fbsdev"):
            raise ValueError(f"не похоже на проект C4: {self.dir}")

    @property
    def app_path(self):
        return _app_of(self.dir)

    @property
    def app_dir(self):
        """Реальное содержимое приложения (папка с ^)."""
        return self.app_path + "^"

    def files(self, suffix=None):
        """Список файлов кода приложения, опционально по суффиксу ('.prg.st')."""
        out = []
        for root, _dirs, names in os.walk(self.app_dir):
            for n in names:
                if suffix is None or n.endswith(suffix):
                    out.append(os.path.join(root, n))
        return sorted(out)

    def read(self, rel_path):
        """Читает файл приложения по пути относительно папки проекта."""
        with open(os.path.join(self.dir, rel_path), encoding="utf-8") as f:
            return f.read()

    def write(self, rel_path, content):
        """Пишет файл приложения (создаёт папки). Бэкап не делает — делайте сами."""
        p = os.path.join(self.dir, rel_path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)

    def compile(self, target_dir=None, verbose=False):
        return compile_app(self.dir, target_dir, verbose=verbose)

    def __repr__(self):
        return f"<C4Project {self.name}>"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python c4_build.py <project.fbsdev>")
    proj = sys.argv[1]
    ok, diags, out = compile_app(proj)
    print(f"compile ok: {ok}")
    for d in diags:
        print(" ", d)
