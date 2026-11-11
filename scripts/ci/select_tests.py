"""Chooses the tests a pull request runs (rules/reference/cicd.md, "The pipelines").

The tests of each changed module and of the modules that depend on it, plus the e2e
tests. A shared module or a file outside every module runs the whole suite.

Usage: git diff --name-only <base> HEAD | python3 scripts/ci/select_tests.py
"""

import ast
import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

WHOLE_SUITE = ['tests']
SHARED_MODULES = {'core', 'common'}
MODULE_TEST_DIRS = ('tests/unit/apps', 'tests/integration/apps')
E2E_DIR = 'tests/e2e'


def select_tests(changed_files: Iterable[str], root: Path) -> list[str]:
    modules = set()
    for path in changed_files:
        if path.startswith(f'{E2E_DIR}/'):
            continue
        module = _module_of(path)
        if module is None or module in SHARED_MODULES:
            return WHOLE_SUITE
        modules.add(module)
    affected = _with_dependents(modules, _dependents(root))
    paths = _existing_test_dirs(affected, root)
    if (root / E2E_DIR).is_dir():
        paths.append(E2E_DIR)
    return paths or WHOLE_SUITE


def _module_of(path: str) -> str | None:
    """`apps/<module>/…` or `tests/<kind>/apps/<module>/…`; None for anything else."""
    parts = Path(path).parts
    if parts[:1] == ('apps',) and len(parts) > 2:
        return parts[1]
    if parts[:1] == ('tests',) and parts[2:3] == ('apps',) and len(parts) > 4:
        return parts[3]
    return None


def _dependents(root: Path) -> dict[str, set[str]]:
    """For each module, the modules that import it (the code is the source)."""
    dependents = defaultdict(set)
    for module_dir in (root / 'apps').iterdir():
        if module_dir.is_dir():
            for imported in _imported_modules(module_dir) - {module_dir.name}:
                dependents[imported].add(module_dir.name)
    return dependents


def _imported_modules(module_dir: Path) -> set[str]:
    imported = set()
    for file in module_dir.rglob('*.py'):
        for node in ast.walk(ast.parse(file.read_text(encoding='utf-8'))):
            imported.update(_apps_modules_in(node))
    return imported


def _apps_modules_in(node: ast.AST) -> set[str]:
    if isinstance(node, ast.Import):
        names = [alias.name for alias in node.names]
    elif isinstance(node, ast.ImportFrom) and node.module == 'apps':
        names = [f'apps.{alias.name}' for alias in node.names]
    elif isinstance(node, ast.ImportFrom) and node.module:
        names = [node.module]
    else:
        return set()
    return {name.split('.')[1] for name in names if name.startswith('apps.')}


def _with_dependents(modules: set[str], dependents: dict[str, set[str]]) -> set[str]:
    affected = set(modules)
    pending = list(modules)
    while pending:
        for dependent in dependents[pending.pop()] - affected:
            affected.add(dependent)
            pending.append(dependent)
    return affected


def _existing_test_dirs(modules: set[str], root: Path) -> list[str]:
    return [
        f'{base}/{module}'
        for module in sorted(modules)
        for base in MODULE_TEST_DIRS
        if (root / base / module).is_dir()
    ]


def main() -> None:
    changed_files = [line.strip() for line in sys.stdin if line.strip()]
    print(' '.join(select_tests(changed_files, Path.cwd())))


if __name__ == '__main__':
    main()
