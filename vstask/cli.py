import argparse
import sys
from .__version__ import VERSION

is_completable = {}
is_terminal = {'-h': True, '--help': True}
parser = argparse.ArgumentParser()
parser.add_argument('tasks', nargs='*', metavar='TASK')


def __keys_filter__(d, c=True):
    return [k for k, v in d.items() if v == c]


def completable():
    return __keys_filter__(is_completable)


def terminal():
    return __keys_filter__(is_terminal)


def register(
    *args,
    **kwargs
):
    terminal = kwargs.pop('terminal', False)
    completable = kwargs.pop('completable', False)
    parser.add_argument(*args, **kwargs)
    is_terminal[args[0]] = terminal
    if len(args) == 2:
        is_terminal[args[1]] = terminal
        is_completable[args[0]] = False
        is_completable[args[1]] = completable
    else:
        is_completable[args[0]] = completable


register(
    '--version',
    action='version',
    help='print version information',
    version='%(prog)s {} for Python {}'.format(
        VERSION,
        sys.version.split('\n')[0],
    ),
    completable=True,
    terminal=True,
)
register(
    '-l', '--list',
    action='store_true',
    help='list available tasks',
    completable=True,
    terminal=True,
)
register(
    '-t', '--time',
    action='store_true',
    help='print runtime information',
    completable=True,
)
register(
    '--completion',
    action='store_true',
    help='bash tab-completion; usage: source <(vstask --completion)',
)


class InputVarsAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        d = getattr(namespace, self.dest, None) or {}
        for item in values:
            if '=' not in item:
                parser.error(f'--input values must be in KEY=VALUE format, got: {item!r}')
            key, _, value = item.partition('=')
            d[key] = value
        setattr(namespace, self.dest, d)


register(
    '-i', '--input',
    dest='input_vars',
    nargs='+',
    metavar='KEY=VALUE',
    action=InputVarsAction,
    default={},
    help='set input variables for the task, e.g. -i buildConfig=Debug buildVariant=CRC_32',
)
