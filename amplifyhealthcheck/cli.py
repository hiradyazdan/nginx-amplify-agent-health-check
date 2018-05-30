import argparse
import pkg_resources

from . import configure
from healthcheck import AmplifyAgentHealthCheck


def init_cli():
    public_methods = verification_methods()
    args = cli_args()

    public_methods = [
        method for method in public_methods
        if not method.startswith('verify_all_')
        and method not in args.get('skip_methods', [])
    ]

    try:
        amphc = configure(**args)

        for method in args.get('skip_methods', public_methods):
            callable(getattr(amphc, method))

        for method in args.get('methods', public_methods):
            getattr(amphc, method)()

        return True
    except AttributeError, exc:
        amphc.decorate_mode = False
        amphc.pretty_print(exc, 'error', False)

        return False


def cli_args():
    version = pkg_resources.require('nginx-amplify-agent-health-check')[0].version
    public_methods = verification_methods()
    epilog_content = []

    for i, vm in enumerate(public_methods):
        epilog_content.append('%s) %s' % (i + 1, vm))

    parser = argparse.ArgumentParser(
        prog='amphc',
        usage=None,
        description='Static and Dynamic Analysis for nginx-amplify-agent Health Status',
        epilog='''
verification methods:
---------------------
  {}
'''.format('\n\t'.expandtabs(2).join(epilog_content)),
        parents=[],
        formatter_class=argparse.RawTextHelpFormatter,
        prefix_chars='-',
        fromfile_prefix_chars=None,
        argument_default=argparse.SUPPRESS,
        conflict_handler='resolve',
        add_help=True
    )

    group = parser.add_mutually_exclusive_group()

    parser.add_argument(
        '-V', '--version',
        dest='version',
        action='version',
        version='This is %(prog)s version ' + version,
        help="show amphc version number"
    )

    parser.add_argument(
        '-v', '--verbose',
        dest='verbose', action='store_true',  help='show all check logs'
    )
    parser.add_argument(
        '-d', '--plain',
        dest='decorate_mode', action='store_false', help='suppress decorating logs'
    )

    parser.add_argument(
        '-c', '--config',
        dest='config_file', action='store', help='set configuration file path (i.e. in ini format)'
    )

    group.add_argument(
        '-x', '--skip',
        dest='skip_methods', action='store', nargs='+', help='specify methods to skip running'
    )

    group.add_argument(
        '-m', '--methods',
        dest='methods', action='store', nargs='+', help='specify methods to run'
    )

    args = vars(parser.parse_args())

    return args


def verification_methods():
    amphc = AmplifyAgentHealthCheck

    methods = [
        method for method in dir(amphc)
        if callable(getattr(amphc, method))
        and method.startswith('verify_')
        and not method.startswith('_')
    ]

    return sorted(set(methods))
