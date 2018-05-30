import mock
import pytest
import StringIO
import sys

from amplifyhealthcheck.cli import init_cli, cli_args
from unittest import TestCase

xfail = pytest.mark.xfail


class ConsoleTestCase(TestCase):
    # @xfail
    # @pytest.mark.focus
    @mock.patch('sys.exit')
    @mock.patch('atexit.register')
    @mock.patch('amplifyhealthcheck.cli.AmplifyAgentHealthCheck.verify_method1', create=True, return_value=None)
    @mock.patch('amplifyhealthcheck.cli.AmplifyAgentHealthCheck.verify_method2', create=True, return_value=None)
    @mock.patch('amplifyhealthcheck.cli.verification_methods')
    @mock.patch('amplifyhealthcheck.cli.cli_args')
    def test_init_cli(self, cli_args_mock, methods_mock, method2_mock, method1_mock, register_mock, exit_mock):
        exit_mock.return_value = mock.MagicMock()
        register_mock.return_value = mock.MagicMock()
        method1_mock.return_value = mock.MagicMock()
        method2_mock.return_value = mock.MagicMock()
        methods_mock.return_value = ['verify_method1', 'verify_method2']

        # skip methods exceptions
        cli_args_mock.return_value = {
            'skip_methods': ['verify_method3']
        }

        self.assertFalse(init_cli())

        # skip methods
        cli_args_mock.return_value = {
            'skip_methods': ['verify_method1', 'verify_method2']
        }

        self.assertTrue(init_cli())

        # specify methods exceptions
        cli_args_mock.return_value = {
            'methods': ['verify_method3']
        }

        self.assertFalse(init_cli())

        # specify methods
        cli_args_mock.return_value = {
            'methods': ['verify_method1', 'verify_method2']
        }

        self.assertTrue(init_cli())

    # @xfail
    # @pytest.mark.focus
    @mock.patch('pkg_resources.require')
    @mock.patch('sys.exit')
    def test_cli_args(self, exit_mock, require_mock):
        require_mock.return_value[0].version = '1.0.0'
        exit_mock.return_value = mock.MagicMock()

        # get version
        with mock.patch('sys.argv', ['amphc', '-V']):
            orig_output = sys.stderr
            sys.stderr = StringIO.StringIO()

            cli_args()

            output = sys.stderr.getvalue().strip()
            sys.stderr.close()
            sys.stderr = orig_output

        assert output == 'This is amphc version 1.0.0'

        # output verbose
        with mock.patch('sys.argv', ['amphc', '-v']):
            parser_args = cli_args()

        self.assertTrue(parser_args['verbose'])

        # no decorate - plain output
        with mock.patch('sys.argv', ['amphc', '-d']):
            parser_args = cli_args()

        self.assertFalse(parser_args['decorate_mode'])

        # set config file
        with mock.patch('sys.argv', ['amphc', '-c', './config.cfg']):
            parser_args = cli_args()

        assert parser_args['config_file'] == './config.cfg'

        # skip methods to run
        with mock.patch('sys.argv', ['amphc', '-x', 'verify_method1', 'verify_method2']):
            parser_args = cli_args()

        assert parser_args['skip_methods'] == ['verify_method1', 'verify_method2']

        # specify methods to run
        with mock.patch('sys.argv', ['amphc', '-m', 'verify_method1', 'verify_method2']):
            parser_args = cli_args()

        assert parser_args['methods'] == ['verify_method1', 'verify_method2']
