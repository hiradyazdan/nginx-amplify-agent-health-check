import pytest

from amplifyhealthcheck.cmd import main
from unittest import TestCase

xfail = pytest.mark.xfail


class TestConsole(TestCase):

    @xfail
    # @pytest.mark.focus
    def test_main(self):
        pass

