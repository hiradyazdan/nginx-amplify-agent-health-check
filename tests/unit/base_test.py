import mock
import pytest
import numpy as np


from amplifyhealthcheck.base import Base
from unittest import TestCase

xfail = pytest.mark.xfail


class BaseTestCase(TestCase):
    def setup_method(self, method):
        pass

    def teardown_method(self, method):
        pass

    # @xfail
    @mock.patch('os.stat')
    def test_file_change_timestamp(self, stat_mock):
        base = Base()
        fp = 'test_dir/timestamp_test_file.txt'

        stat_mock.return_value = mock.Mock(st_mtime=1526655235)
        expected_timestamp = 1526655235

        assert base.file_change_timestamp(fp) == expected_timestamp

    # @xfail
    def test_file_name(self):
        base = Base()
        file_path = 'test_dir/test_file.txt'
        expected_file_name = 'test_file.txt'

        assert base.file_name(file_path) == expected_file_name

    # @xfail
    @mock.patch('os.walk')
    def test_dir_tree(self, walk_mock):
        base = Base()
        dir_path = 'test_dir'
        file_ext = '.rst'

        walk_mock.return_value = [
            ('test_dir', ('test_sub_dir', 'test_sub_dir_2'), ()),
            ('test_dir/test_sub_dir', (), ('test_file.txt', 'test_file_rst.rst')),
            ('test_dir/test_sub_dir_2', (), ('test_file_2.txt', 'test_file_rst_2.rst'))
        ]

        exp_tree_w_ext = [
            'test_dir/test_sub_dir_2', 'test_dir/test_sub_dir',
            'test_dir/test_sub_dir/test_file_rst.rst',
            'test_dir/test_sub_dir_2/test_file_rst_2.rst'
        ]

        exp_tree_no_ext = [
            'test_dir/test_sub_dir_2', 'test_dir/test_sub_dir',
            'test_dir/test_sub_dir/test_file.txt',
            'test_dir/test_sub_dir/test_file_rst.rst',
            'test_dir/test_sub_dir_2/test_file_2.txt',
            'test_dir/test_sub_dir_2/test_file_rst_2.rst'
        ]

        np.testing.assert_array_equal(sorted(base.dir_tree(dir_path, file_ext)), sorted(exp_tree_w_ext))
        np.testing.assert_array_equal(sorted(base.dir_tree(dir_path)),           sorted(exp_tree_no_ext))

    # @xfail
    @mock.patch('os.path')
    def test_files(self, path_mock):
        base = Base()
        wildcard_file_path = 'test_sub_dir/*.rst'

        path_mock.split.return_value = ['test_dir/test_sub_dir/', 'test_file_rst_1.rst']
        path_mock.join.return_value = '{0}{1}'.format(path_mock.split.return_value[0], path_mock.split.return_value[1])

        exp_files = [
            'test_dir/test_sub_dir/test_file_rst_1.rst',
        ]

        np.testing.assert_array_equal(sorted(base.files(wildcard_file_path)), sorted(exp_files))

    @xfail
    def test_pid(self):
        pass

    @xfail
    def test_all_pids(self):
        pass

    @xfail
    def test_ps_name(self):
        pass

    @xfail
    def test_ps_path(self):
        pass

    @xfail
    def test_ps_owner(self):
        pass

    @xfail
    def test_current_user(self):
        pass

    @xfail
    def test_check_ps_access(self):
        pass

    # @xfail
    @mock.patch('os.path.exists')
    def test_check_file(self, exists_mock):
        base = Base()
        existing_file_path = 'test_dir/test_sub_dir/test_file.txt'
        non_ex_file_path = 'test_dir/test_sub_dir/no_test_file.txt'

        exists_mock.return_value = True
        assert base.check_file(existing_file_path) is True

        exists_mock.return_value = False
        assert base.check_file(non_ex_file_path) is False

    @xfail
    def test_check_file_perms(self):
        pass

    # @xfail
    @mock.patch('__builtin__.open', new_callable=mock.mock_open, read_data="this is a test\nthis is a test")
    def test_read_file(self, open_mock):
        base = Base()
        file_path = 'test_dir/test_sub_dir/test_file.txt'

        exp_file_content = [
            'this is a test',
            'this is a test'
        ]

        self.assertEqual(sorted(base.read_file(file_path)), sorted(exp_file_content))

    @xfail
    def test_stat(self):
        pass





