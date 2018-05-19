import os
import mock
import pytest

from amplifyhealthcheck.healthcheck import AmplifyAgentHealthCheck
from unittest import TestCase

xfail = pytest.mark.xfail


class HealthChckTestCase(TestCase):

    # @classmethod
    @mock.patch('os.stat')
    def setup_class(cls, stat_mock):
        amplify_agent_path = 'tests/fixtures/agent_files/nginx-amplify-agent'
        amplify_conf_file = 'tests/fixtures/agent_files/etc/amplify-agent/agent.conf'
        amplify_log_file = 'tests/fixtures/agent_files/var/log/amplify-agent/agent.log'
        amplify_pid_file = 'tests/fixtures/agent_files/var/run/amplify-agent/amplify-agent.pid'

        nginx_all_confs_path = '/etc/nginx'
        nginx_conf_file = 'tests/fixtures/nginx_files/etc/nginx/nginx.conf'
        nginx_status_conf_file = 'tests/fixtures/nginx_files/etc/nginx/conf.d/stub_status.conf'
        nginx_mime_types_file = 'tests/fixtures/nginx_files/etc/nginx/mime.types'
        nginx_sites_available_conf_files = 'tests/fixtures/nginx_files/etc/nginx/sites-available/*.conf'
        nginx_sites_enabled_conf_files = 'tests/fixtures/nginx_files/etc/nginx/sites-enabled/*.conf'
        nginx_pid_file = 'tests/fixtures/nginx_files/var/run/nginx.pid'
        nginx_log_files = 'tests/fixtures/nginx_files/var/log/nginx/*.log'

        stat_mock.return_value = mock.Mock(st_uid=os.getuid())

        cls.healthcheck = AmplifyAgentHealthCheck(
            verbose=True,
            decorate_mode=False,
            heading='Amplify Agent Health Check Analysis',

            # Amplify
            amplify_agent_path=amplify_agent_path,
            amplify_conf_file=amplify_conf_file,
            amplify_log_file=amplify_log_file,
            amplify_pid_file=amplify_pid_file,

            # Nginx
            nginx_all_confs_path=nginx_all_confs_path,
            nginx_conf_file=nginx_conf_file,
            nginx_status_conf_file=nginx_status_conf_file,
            nginx_sites_available_conf_files=nginx_sites_available_conf_files,
            nginx_sites_enabled_conf_files=nginx_sites_enabled_conf_files,
            nginx_mime_types_file=nginx_mime_types_file,
            nginx_log_files=nginx_log_files,
            nginx_pid_file=nginx_pid_file,

            # System
            max_time_diff_allowance=80
        )#.generate_output()

    @classmethod
    def teardown_class(cls):
        pass

    @xfail
    @mock.patch('subprocess.Popen')
    def test_verify_sys_pkgs(self, popen_mock):
        packages = [
            'python', 'python-dev',
            'git',
            'util-linux', 'procps',
            'curl',  # 'wget',
            'gcc', 'musl-dev', 'linux-headers'
        ]

        find_sys_pkg_cmd=['apk', 'info']

        process_mock = mock.Mock()
        attrs = {}
        process_mock.configure_mock(**attrs)

        for pkg in packages:
            popen_mock(find_sys_pkg_cmd + [pkg]).return_value = process_mock
            self.assertTrue(popen_mock.assert_called_with(find_sys_pkg_cmd + [pkg]))

        fail_count = 0

        self.healthcheck.verify_sys_pkgs(packages, find_sys_pkg_cmd, fail_count)

    @xfail
    def test_verify_py_pkgs(self):
        pass

    @xfail
    def test_verify_all_packages(self):
        apk_packages = [
            'python', 'python-dev',
            'git',
            'util-linux', 'procps',
            'curl',  # 'wget',
            'gcc', 'musl-dev', 'linux-headers'
        ]

        requirements_file = '/packages/nginx-amplify-agent/requirements'

        self.healthcheck.verify_all_packages(apk_packages, requirements_file, find_sys_pkg_cmd=['apk', 'info'])

    @xfail
    def test_verify_agent_log(self):
        pass

    @xfail
    def test_verify_agent_user(self):
        pass

    @xfail
    def test_verify_ngx_start_path(self):
        pass

    @xfail
    def test_verify_sys_ps_access(self):
        pass

    @xfail
    def test_verify_sys_time(self):
        pass

    @xfail
    def test_verify_ngx_stub_status(self):
        pass

    @xfail
    def test_verify_ngx_logs_read_access(self):
        pass

    @xfail
    def test_verify_ngx_config_files_access(self):
        pass

    @xfail
    def test_verify_metrics_format(self):
        pass

    @xfail
    def test_verify_dns_resolver(self):
        pass

    @xfail
    def test_verify_outbound_tls_access(self):
        pass

    @xfail
    def test_verify_metrics_collection(self):
        pass

    @xfail
    def test_pretty_print(self):
        pass

    @xfail
    def test_verify_proc_sys_access(self):
        pass




