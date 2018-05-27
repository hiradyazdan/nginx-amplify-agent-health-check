import mock
import pytest

from datetime import datetime, timedelta
from amplifyhealthcheck.healthcheck import AmplifyAgentHealthCheck
from unittest import TestCase

# Package Exceptions
from pkg_resources import DistributionNotFound, VersionConflict
from psutil import AccessDenied
from ntplib import NTPException
from socket import gaierror
from requests.exceptions import ConnectionError

xfail = pytest.mark.xfail

amplify_agent_path = 'tests/fixtures/agent_files/nginx-amplify-agent'
amplify_reqs_file = '/requirements'
amplify_conf_file = 'tests/fixtures/agent_files/etc/amplify-agent/agent.conf'
amplify_log_file = 'tests/fixtures/agent_files/var/log/amplify-agent/agent.log'
amplify_pid_file = 'tests/fixtures/agent_files/var/run/amplify-agent/amplify-agent.pid'

nginx_all_confs_path = 'tests/fixtures/nginx_files/etc/nginx'
nginx_conf_file = 'tests/fixtures/nginx_files/etc/nginx/nginx.conf'
nginx_status_conf_file = 'tests/fixtures/nginx_files/etc/nginx/conf.d/stub_status.conf'
nginx_mime_types_file = 'tests/fixtures/nginx_files/etc/nginx/mime.types'
nginx_sites_available_conf_files = 'tests/fixtures/nginx_files/etc/nginx/sites-available/*.conf'
nginx_sites_enabled_conf_files = 'tests/fixtures/nginx_files/etc/nginx/sites-enabled/*.conf'
nginx_pid_file = 'tests/fixtures/nginx_files/var/run/nginx.pid'
nginx_log_files = 'tests/fixtures/nginx_files/var/log/nginx/*.log'
nginx_additional_metrics = [
    'sn="$server_name"',
    'rt=$request_time',
    'ua="$upstream_addr"',
    'us="$upstream_status"',
    'ut="$upstream_response_time"',
    'ul="$upstream_response_length"',
    'cs=$upstream_cache_status'
]

system_packages = [
    'python', 'python-dev',
    'git',
    'util-linux', 'procps',
    'curl',  # 'wget',
    'gcc', 'musl-dev', 'linux-headers'
]
system_find_package_command = ['apk', 'info']


class HealthChckTestCase(TestCase):
    @classmethod
    def setup_class(cls):
        cls.healthcheck = AmplifyAgentHealthCheck(
            verbose=True,
            decorate_mode=True,
            heading='Amplify Agent Health Check Analysis',

            # Amplify
            amplify_agent_path=amplify_agent_path,
            amplify_reqs_file=amplify_reqs_file,
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
            nginx_additional_metrics=nginx_additional_metrics,

            # System
            system_packages=system_packages,
            system_find_package_command=system_find_package_command,
            system_time_diff_max_allowance=80
        )

    @classmethod
    def teardown_class(cls):
        pass

    @mock.patch('os.stat')
    @mock.patch('psutil.Process')
    @mock.patch('pwd.getpwuid')
    @mock.patch('amplifyhealthcheck.healthcheck.AmplifyAgentHealthCheck.pid')
    def setup_method(self, method, pid_method_mock, getpwuid_mock, process_mock, os_stat_mock):
        os_stat_mock.return_value = mock.MagicMock(st_uid=120)
        getpwuid_mock.return_value = mock.MagicMock(pw_name='permitted_user')  # nginx
        pid_method_mock.return_value = mock.MagicMock()
        process_mock.return_value.name.return_value = 'amplify-agent'

        self.healthcheck.configure()

    def teardown_method(self, method):
        self.healthcheck.verbose = True
        self.healthcheck.ngx_all_confs_path = nginx_all_confs_path
        self.healthcheck.ngx_conf_file = nginx_conf_file
        self.healthcheck.ngx_log_files = nginx_log_files
        self.healthcheck.ngx_conf_blocks = []

    # @xfail
    # @pytest.mark.focus
    @mock.patch('subprocess.Popen')
    def test_verify_sys_pkgs(self, popen_mock):
        popen_mock.return_value.wait.return_value = 0
        fail_count = self.healthcheck.verify_sys_pkgs()

        assert fail_count == 0

        popen_mock.side_effect = OSError(Exception, 'No such file or directory')
        fail_count = self.healthcheck.verify_sys_pkgs()

        assert fail_count > 0

        popen_mock.side_effect = None
        popen_mock.return_value.wait.return_value = 1
        fail_count = self.healthcheck.verify_sys_pkgs()

        assert fail_count > 0

    # @xfail
    # @pytest.mark.focus
    @mock.patch('pkg_resources.find_distributions')
    @mock.patch('pkg_resources.require')
    def test_verify_py_pkgs(self, require_mock, find_dist_mock):
        find_dist_mock.return_value = [
            'gevent==1.1.0',
            'lockfile==0.11.0',
            'netaddr==0.7.18',
            'netifaces==0.10.4',
            'psutil==4.0.0',
            'requests==2.12.4',
            'ujson==1.33',
            'python-daemon==2.0.6',
            'setproctitle==1.1.10',
            'rstr==2.2.3',
            'flup==1.0.2',
            'scandir==1.5',
            'crossplane==0.3.1',
            'PyMySQL==0.7.11'
        ]
        fail_count = self.healthcheck.verify_py_pkgs()

        assert fail_count == 0

        find_dist_mock.return_value = [
            'gevent==1.1.0',
            'lockfile==0.11.0',
            'netaddr==0.7.18',
            'netifaces==0.10.4',
            'psutil==4.0.0',
            'requests==2.12.4',
            'ujson==1.33'
        ]
        require_mock.side_effect = DistributionNotFound(Exception, 'distribution not found')
        fail_count = self.healthcheck.verify_py_pkgs()

        assert fail_count > 0

    # @xfail
    # @pytest.mark.focus
    @mock.patch('pkg_resources.find_distributions')
    @mock.patch('subprocess.Popen')
    @mock.patch('amplifyhealthcheck.healthcheck.AmplifyAgentHealthCheck.check_file')
    def test_verify_all_packages(self, check_file_mock, popen_mock, find_dist_mock):
        check_file_mock.return_value = True
        find_dist_mock.return_value = [
            'gevent==1.1.0',
            'lockfile==0.11.0',
            'netaddr==0.7.18',
            'netifaces==0.10.4',
            'psutil==4.0.0',
            'requests==2.12.4',
            'ujson==1.33',
            'python-daemon==2.0.6',
            'setproctitle==1.1.10',
            'rstr==2.2.3',
            'flup==1.0.2',
            'scandir==1.5',
            'crossplane==0.3.1',
            'PyMySQL==0.7.11'
        ]
        popen_mock.return_value.wait.return_value = 0
        self.healthcheck.verbose = False
        fail_count = self.healthcheck.verify_all_packages()

        assert fail_count == 0

        check_file_mock.return_value = False
        fail_count = self.healthcheck.verify_all_packages()

        assert fail_count > 0

    # @xfail
    # @pytest.mark.focus
    def test_verify_agent_ps(self):
        self.healthcheck.amp_pid = 100
        fail_count = self.healthcheck.verify_agent_ps()

        assert fail_count == 0

        self.healthcheck.amp_pid = None
        fail_count = self.healthcheck.verify_agent_ps()

        assert fail_count > 0

    # @xfail
    # @pytest.mark.focus
    @mock.patch('os.path.exists')
    @mock.patch('amplifyhealthcheck.healthcheck.AmplifyAgentHealthCheck.read_file')
    def test_verify_agent_log(self, read_file_mock, path_exists_mock):
        path_exists_mock.return_value = True
        read_file_mock.return_value = ['line 1', 'line 2']
        fail_count = self.healthcheck.verify_agent_log()

        assert fail_count == 0

        path_exists_mock.return_value = False
        fail_count = self.healthcheck.verify_agent_log()

        assert fail_count > 0

        path_exists_mock.return_value = True
        read_file_mock.return_value = []
        fail_count = self.healthcheck.verify_agent_log()

        assert fail_count > 0

    # @xfail
    # @pytest.mark.focus
    def test_verify_agent_user(self):
        self.healthcheck.amp_owner = self.healthcheck.ngx_worker_onwer = 'permitted_user'

        fail_count = self.healthcheck.verify_agent_user()

        assert fail_count == 0

        self.healthcheck.amp_owner = self.healthcheck.ngx_worker_onwer = None

        fail_count = self.healthcheck.verify_agent_user()

        assert fail_count > 0

        self.healthcheck.amp_owner = 'not_permitted_user'
        self.healthcheck.ngx_worker_onwer = 'permitted_user'

        fail_count = self.healthcheck.verify_agent_user()

        assert fail_count > 0

    # @xfail
    # @pytest.mark.focus
    @mock.patch('os.path.isabs')
    @mock.patch('psutil.Process')
    def test_verify_ngx_master_ps(self, process_mock, is_abs_mock):
        process_mock.return_value.ppid.return_value = 1
        fail_count = self.healthcheck.verify_ngx_master_ps()

        assert fail_count == 0

        self.healthcheck.ngx_pid = None
        fail_count = self.healthcheck.verify_ngx_master_ps()

        assert fail_count > 0

        self.healthcheck.ngx_pid = '100'
        process_mock.return_value.ppid.return_value = 87
        fail_count = self.healthcheck.verify_ngx_master_ps()

        assert fail_count > 0

        process_mock.return_value.ppid.return_value = 1
        is_abs_mock.return_value = True
        process_mock.return_value.exe.return_value = 'some_absolute_path'
        fail_count = self.healthcheck.verify_ngx_master_ps()

        assert fail_count == 0

        is_abs_mock.return_value = False
        process_mock.return_value.exe.return_value = 'some_relative_path'
        fail_count = self.healthcheck.verify_ngx_master_ps()

        assert fail_count > 0

    # @xfail
    # @pytest.mark.focus
    @mock.patch('psutil.pids')
    def test_verify_sys_ps_access(self, pids_mock):
        pids_mock.return_value = [100, 120]
        fail_count = self.healthcheck.verify_sys_ps_access()

        assert fail_count == 0

        pids_mock.side_effect = AccessDenied(Exception, 'No Access')
        fail_count = self.healthcheck.verify_sys_ps_access()

        assert fail_count > 0

    # @xfail
    # @pytest.mark.focus
    @mock.patch('ntplib.NTPClient.request')
    @mock.patch('amplifyhealthcheck.healthcheck.AmplifyAgentHealthCheck.datetime_now')
    def test_verify_sys_time(self, datetime_now_mock, request_mock):
        now_datetime = datetime(2018, 5, 27, 12, 58, 59, 504275)
        now_timestamp = 1527425939.5042753

        request_mock.return_value = mock.MagicMock(tx_time=now_timestamp)
        datetime_now_mock.return_value = now_datetime + timedelta(
            seconds=self.healthcheck.sys_time_diff_max_allowance
        )
        fail_count = self.healthcheck.verify_sys_time()

        assert fail_count == 0

        request_mock.return_value = mock.MagicMock(tx_time=now_timestamp)
        datetime_now_mock.return_value = now_datetime + timedelta(
            seconds=self.healthcheck.sys_time_diff_max_allowance + 1
        )
        fail_count = self.healthcheck.verify_sys_time()

        assert fail_count > 0

        request_mock.side_effect = NTPException(Exception, 'No response received from pool.ntp.org')
        fail_count = self.healthcheck.verify_sys_time()

        assert fail_count > 0

    # @xfail
    # @pytest.mark.focus
    @mock.patch('os.path.exists')
    @mock.patch('amplifyhealthcheck.healthcheck.Popen')
    def test_verify_ngx_stub_status(self, popen_mock, path_exists_mock):
        path_exists_mock.return_value = True
        popen_mock.return_value.communicate.return_value = (
            'http_dav_module\nhttp_ssl_module\nhttp_stub_status_module\nhttp_gzip_static_module\nhttp_v2_module',
            ''
        )

        fail_count = self.healthcheck.verify_ngx_stub_status()

        assert fail_count == 0

        self.healthcheck.verbose = False
        path_exists_mock.return_value = True
        popen_mock.return_value.communicate.return_value = (
            'http_dav_module\nhttp_ssl_module\nhttp_stub_status_module\nhttp_gzip_static_module\nhttp_v2_module',
            ''
        )

        fail_count = self.healthcheck.verify_ngx_stub_status()

        assert fail_count == 0

        path_exists_mock.return_value = False
        popen_mock.return_value.communicate.return_value = (
            'http_dav_module\nhttp_ssl_module\nhttp_stub_status_module\nhttp_gzip_static_module\nhttp_v2_module',
            ''
        )
        fail_count = self.healthcheck.verify_ngx_stub_status()

        assert fail_count > 0

        path_exists_mock.return_value = True

        popen_mock.return_value.communicate.return_value = (
            'http_dav_module\nhttp_ssl_module\nhttp_gzip_static_module\nhttp_v2_module',
            'error'
        )
        fail_count = self.healthcheck.verify_ngx_stub_status()

        assert fail_count > 0

        path_exists_mock.return_value = True
        popen_mock.return_value.communicate.return_value = (
            'http_dav_module\nhttp_ssl_module\nhttp_stub_status_module\nhttp_gzip_static_module\nhttp_v2_module',
            ''
        )
        self.teardown_method(None)
        self.healthcheck.ngx_conf_file = 'tests/fixtures/nginx_files/etc/nginx/nginx.conf.missing'
        self.setup_method(None)
        fail_count = self.healthcheck.verify_ngx_stub_status()

        assert fail_count > 0

    # @xfail
    # @pytest.mark.focus
    @mock.patch('pwd.getpwuid')
    def test_verify_ngx_logs_read_access(self, getpwuid_mock):
        getpwuid_mock.return_value = mock.MagicMock(pw_name='permitted_user')  # nginx
        fail_count = self.healthcheck.verify_ngx_logs_read_access()

        assert fail_count == 0

        self.healthcheck.verbose = False
        getpwuid_mock.return_value = mock.MagicMock(pw_name='permitted_user')  # nginx
        fail_count = self.healthcheck.verify_ngx_logs_read_access()

        assert fail_count == 0

        getpwuid_mock.return_value = mock.MagicMock(pw_name='not_permitted_user')
        fail_count = self.healthcheck.verify_ngx_logs_read_access()

        assert fail_count > 0

        self.teardown_method(None)
        self.healthcheck.ngx_log_files = '/path_does_not_exist'
        self.setup_method(None)
        fail_count = self.healthcheck.verify_ngx_logs_read_access()

        assert fail_count > 0

    # @xfail
    # @pytest.mark.focus
    @mock.patch('pwd.getpwuid')
    @mock.patch('os.stat')
    def test_verify_ngx_config_files_access(self, os_stat_mock, getpwuid_mock):
        getpwuid_mock.return_value = mock.MagicMock(pw_name='permitted_user')  # nginx
        fail_count = self.healthcheck.verify_ngx_config_files_access()

        assert fail_count == 0

        self.healthcheck.verbose = False
        getpwuid_mock.return_value = mock.MagicMock(pw_name='permitted_user')  # nginx
        fail_count = self.healthcheck.verify_ngx_config_files_access()

        assert fail_count == 0

        getpwuid_mock.return_value = mock.MagicMock(pw_name='not_permitted_user')
        os_stat_mock.return_value = mock.MagicMock(st_mode=0)
        fail_count = self.healthcheck.verify_ngx_config_files_access()

        assert fail_count > 0

        self.teardown_method(None)
        self.healthcheck.ngx_all_confs_path = '/path_does_not_exist'
        self.setup_method(None)
        fail_count = self.healthcheck.verify_ngx_config_files_access()

        assert fail_count > 0

    # @xfail
    # @pytest.mark.focus
    def test_verify_ngx_metrics(self):
        fail_count = self.healthcheck.verify_ngx_metrics()

        assert fail_count == 0

        self.healthcheck.verbose = False
        fail_count = self.healthcheck.verify_ngx_metrics()

        assert fail_count == 0

        self.teardown_method(None)
        self.healthcheck.ngx_conf_file = '/path_does_not_exist'
        self.setup_method(None)

        fail_count = self.healthcheck.verify_ngx_metrics()

        assert fail_count > 0

        self.teardown_method(None)
        self.healthcheck.ngx_conf_file = 'tests/fixtures/nginx_files/etc/nginx/nginx.conf.missing'
        self.setup_method(None)

        fail_count = self.healthcheck.verify_ngx_metrics()

        assert fail_count == 2

    @xfail
    # @pytest.mark.focus
    def test_verify_dns_resolver(self):
        pass

    # @xfail
    # @pytest.mark.focus
    @mock.patch('requests.get')
    def test_verify_outbound_tls_access(self, get_mock):
        fail_count = self.healthcheck.verify_outbound_tls_access()
        assert fail_count == 0

        get_mock.side_effect = ConnectionError(Exception, 'No Connection')
        fail_count = self.healthcheck.verify_outbound_tls_access()

        assert fail_count > 0

    @xfail
    # @pytest.mark.focus
    def test_verify_metrics_collection(self):
        pass

    @xfail
    # @pytest.mark.focus
    def test_verify_proc_sys_access(self):
        pass
