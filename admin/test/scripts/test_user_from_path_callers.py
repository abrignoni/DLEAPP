"""User columns come from the path inside the extraction, never from the staged path.

Every artifact that fills a User column with user_from_path (scripts/windows_registry.py
or scripts/macos_plists.py) must hand it the path context.get_relative_path returns. The
staged path begins with the examiner's own report folder, which on macOS and Windows
usually sits under the examiner's Users folder, so a staged path makes every row carry the
examiner's account name instead of the user folder the file came from.
"""
import ast
import pathlib
import sys
import unittest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts import macos_plists, windows_registry  # pylint: disable=wrong-import-position

ARTIFACTS = REPO_ROOT / 'scripts' / 'artifacts'
HELPER = 'user_from_path'


def _is_relative_call(node):
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
            and node.func.attr == 'get_relative_path')


def _relative_names(function):
    """Names the function binds to a get_relative_path result."""
    names = set()
    for node in ast.walk(function):
        if isinstance(node, ast.Assign) and _is_relative_call(node.value):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def _functions(tree):
    return [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _calls_to(function, name):
    return [n for n in ast.walk(function) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name) and n.func.id == name]


def _is_relative(arg, function):
    """A get_relative_path call, or an expression built only from names bound to one."""
    if any(_is_relative_call(node) for node in ast.walk(arg)):
        return True
    names = {node.id for node in ast.walk(arg) if isinstance(node, ast.Name)}
    return bool(names) and names <= _relative_names(function)


def unchecked_calls(source):
    """(line, reason) for each user_from_path call not given a relative path."""
    tree = ast.parse(source)
    functions = _functions(tree)
    problems = []
    for function in functions:
        params = [a.arg for a in function.args.args]
        for call in _calls_to(function, HELPER):
            arg = call.args[0] if call.args else None
            if arg is not None and _is_relative(arg, function):
                continue
            if isinstance(arg, ast.Name) and arg.id in params:
                # One level up: every caller of this function passes a relative path.
                position = params.index(arg.id)
                callers = [(outer, c) for outer in functions
                           for c in _calls_to(outer, function.name)]
                if callers and all(len(c.args) > position and _is_relative(c.args[position], outer)
                                   for outer, c in callers):
                    continue
            problems.append((call.lineno, ast.unparse(arg) if arg is not None else ''))
    return problems


class TestUserFromPathCallers(unittest.TestCase):

    def test_every_caller_passes_the_path_inside_the_extraction(self):
        checked, problems = 0, []
        for path in sorted(ARTIFACTS.glob('*.py')):
            source = path.read_text(encoding='utf-8')
            if f'{HELPER}(' not in source:
                continue
            checked += source.count(f'{HELPER}(')
            problems += [f'{path.name}:{line} passes {arg}'
                         for line, arg in unchecked_calls(source)]
        self.assertGreater(checked, 20)
        self.assertEqual(problems, [])

    def test_no_artifact_keeps_its_own_copy_of_the_helper(self):
        copies = [f'{path.name}:{node.lineno}' for path in sorted(ARTIFACTS.glob('*.py'))
                  for node in _functions(ast.parse(path.read_text(encoding='utf-8')))
                  if node.name.endswith(HELPER)]
        self.assertEqual(copies, [])

    def test_a_staged_path_is_caught(self):
        source = ('def run(context, path):\n'
                  '    relative = context.get_relative_path(path)\n'
                  '    return user_from_path(path), relative\n')
        self.assertEqual(unchecked_calls(source), [(3, 'path')])

    def test_a_relative_path_through_a_helper_function_passes(self):
        source = ('def where(relative):\n'
                  '    return user_from_path(relative)\n'
                  'def run(context, path):\n'
                  '    relative = context.get_relative_path(path)\n'
                  '    return where(relative)\n')
        self.assertEqual(unchecked_calls(source), [])
        self.assertEqual(unchecked_calls(source.replace('where(relative)\n', "where('/' + relative)\n")), [])
        self.assertEqual(unchecked_calls(source.replace('where(relative)\n', 'where(path)\n')),
                         [(2, 'relative')])


class TestUserFromPath(unittest.TestCase):

    def test_the_folder_after_users_in_a_relative_path(self):
        self.assertEqual(windows_registry.user_from_path('lba0/Users/alice/NTUSER.DAT'), 'alice')
        self.assertEqual(windows_registry.user_from_path(r'p3\Users\Default\NTUSER.DAT'), 'Default')
        self.assertEqual(windows_registry.user_from_path('Windows/System32/config/SOFTWARE'), '')
        self.assertEqual(macos_plists.user_from_path('Users/someone/Library/x.plist'), 'someone')

    def test_the_staged_path_names_the_examiner_instead(self):
        staged = '/Users/examiner/Reports/DLEAPP_Reports/data/lba0/Users/alice/NTUSER.DAT'
        self.assertEqual(windows_registry.user_from_path(staged), 'examiner')


if __name__ == '__main__':
    unittest.main()
