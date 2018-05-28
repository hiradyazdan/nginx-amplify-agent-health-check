import mock
import pytest
import sys
import argparse

from amplifyhealthcheck.cli import init_cli
from unittest import TestCase

xfail = pytest.mark.xfail


class ConsoleTestCase(TestCase):
    # @xfail
    # @pytest.mark.focus
    def test_init_cli(self):
        pass
