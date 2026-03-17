#!/usr/bin/env python
import json
import os
import re
import shlex
import subprocess
from .Timer import timed
from . import cli


def get_task_label(task, index):
    if 'label' in task:
        return task['label']
    elif 'group' in task and isinstance(task['group'], str):
        return task['group']
    return 'task{}'.format(index)


def get_tasks():
    old_cwd = os.getcwd()
    try:
        while not os.path.isdir('.vscode'):
            if os.getcwd() == '/':
                raise IOError('.vscode directory not found')
            os.chdir('..')

        with open(os.path.join('.vscode', 'tasks.json')) as f:
            content = f.read()
            # Strip block comments
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            # Strip line comments
            content = re.sub(r'//[^\n]*', '', content)
            tasks = json.loads(content)['tasks']
    except IOError:
        tasks = []
    except json.JSONDecodeError as e:
        print("Invalid tasks.json:")
        print(f'  {str(e)}')
        tasks = []
    root = os.path.abspath(os.getcwd())
    os.chdir(old_cwd)
    return root, {
        get_task_label(task, i): task
        for i, task in enumerate(tasks)
    }


def resolve_variables(s, root, input_vars=None):
    """Substitute VS Code variables in a string."""
    s = s.replace('${workspaceFolder}', root)
    s = s.replace('${workspaceFolderBasename}', os.path.basename(root))
    s = s.replace('${cwd}', os.getcwd())
    if input_vars:
        for key, value in input_vars.items():
            s = s.replace('${input:' + key + '}', value)
    return s


def run_task(task, root='.', input_vars=None):
    options = task.get('options', {})
    cmd = resolve_variables(task['command'], root, input_vars)
    if 'args' in task:
        cmd = shlex.join([
            cmd,
            *[resolve_variables(a, root, input_vars) for a in task.get('args', [])]
        ])
    print(f'> {cmd}')
    cwd = root
    if 'cwd' in options:
        resolved_cwd = resolve_variables(options['cwd'], root, input_vars)
        cwd = resolved_cwd if os.path.isabs(resolved_cwd) else os.path.join(root, resolved_cwd)
    env = None
    if 'env' in options:
        env = os.environ.copy()
        env.update({
            k: resolve_variables(v, root, input_vars)
            for k, v in options['env'].items()
        })
    p = subprocess.Popen(
        ['bash', '--login'],
        stdin=subprocess.PIPE,
        cwd=cwd,
        env=env,
        shell=task.get('type', 'process') == 'shell',
    )
    try:
        p.stdin.write(cmd + '\n')
        p.stdin.write('exit\n')
    except TypeError:
        p.stdin.write((cmd + '\n').encode())
        p.stdin.write('exit\n'.encode())
        p.communicate()
    return p.wait()


def main(args=None):
    opts = cli.parser.parse_args(args)
    root, tasks = get_tasks()

    if opts.completion:
        from .completion import COMPLETION
        print(COMPLETION)
        return 0

    if not tasks and opts.tasks:
        print('Unable to locate .vscode directory or tasks.json')
        return 1

    if opts.list or not opts.tasks:
        for task_name in tasks.keys():
            print(task_name)
        return 0

    with timed(opts.time):
        for task_name in opts.tasks:
            if run_task(tasks[task_name], root, opts.input_vars) != 0:
                return 1
    return 0
