import os
import pkg_resources
import ntplib
import socket
import atexit
import crossplane
import requests

from re import sub
from subprocess import call, Popen, PIPE
from base import Base
from datetime import datetime
from time import sleep

devnull = open(os.devnull, 'w')


class AmplifyAgentHealthCheck(Base):
    def __init__(self, **attrs):
        super(self.__class__, self).__init__()

        self.verbose = attrs['verbose']
        self.decorate_mode = attrs['decorate_mode']
        self.heading = attrs['heading']

        # System
        self.sys_pkgs = attrs['system_packages']
        self.sys_find_pkg_cmd = attrs['system_find_package_command']
        self.sys_time_diff_max_allowance = attrs['system_time_diff_max_allowance']

        # Amplify
        self.amp_agent_path = attrs['amplify_agent_path']
        self.amp_reqs_file = attrs['amplify_reqs_file']
        self.amp_conf_file = attrs['amplify_conf_file']
        self.amp_log_file = attrs['amplify_log_file']
        self.amp_pid_file = attrs['amplify_pid_file']

        self.amp_pid = None
        self.amp_owner = None
        self.amp_ps_name = None

        # Nginx
        self.ngx_all_confs_path = attrs['nginx_all_confs_path']
        self.ngx_conf_file = attrs['nginx_conf_file']
        self.ngx_status_conf_file = attrs['nginx_status_conf_file']
        self.ngx_sites_available_conf_files = attrs['nginx_sites_available_conf_files']
        self.ngx_sites_enabled_conf_files = attrs['nginx_sites_enabled_conf_files']
        self.ngx_mime_types_file = attrs['nginx_mime_types_file']
        self.ngx_log_files = attrs['nginx_log_files']
        self.ngx_pid_file = attrs['nginx_pid_file']
        self.ngx_additional_metrics = attrs['nginx_additional_metrics']

        self.ngx_conf = None
        self.ngx_conf_blocks = []
        self.ngx_pid = None
        self.ngx_owner = None
        self.ngx_worker_pid = None
        self.ngx_worker_onwer = None

    def configure(self):
        try:
            self.amp_pid = self.read_file(self.amp_pid_file)[0]
            self.amp_owner = self.ps_owner(self.amp_pid)
            self.amp_ps_name = self.ps_name(self.amp_pid)

            self.ngx_pid = self.read_file(self.ngx_pid_file)[0]
            self.ngx_owner = self.ps_owner(self.ngx_pid)
            self.ngx_worker_pid = self.pid('nginx: worker process')[0]
            self.ngx_worker_onwer = self.ps_owner(self.ngx_worker_pid)
            self.ngx_conf = crossplane.parse(self.ngx_conf_file)

            for config in self.ngx_conf['config']:
                for parsed in config.get('parsed', []):
                    for block in parsed.get('block', []):
                        self.ngx_conf_blocks.append(block)
        except IOError, exc:
            pass

        return self

    def generate_output(self):
        print '\n----- {0}{1}{2} -----\n'.format(self.cyan_color, self.heading, self.no_color)

        atexit.register(self.decorate)

        return self

    def verify_sys_pkgs(self, fail_count=0):
        fail_count += fail_count

        for pkg in self.sys_pkgs:
            try:
                status = call(self.sys_find_pkg_cmd + [pkg], stdout=devnull, stderr=devnull)

                if status != 0:
                    raise ValueError('{0} package {1} was NOT found'.format(self.sys_find_pkg_cmd[0], pkg))
                elif self.verbose:
                    self.pretty_print('{0} package {1} was found'.format(self.sys_find_pkg_cmd[0], pkg))
            except OSError, exc:
                fail_count += 1
                self.pretty_print('System {} package manager is not installed'
                                  .format(self.sys_find_pkg_cmd[0]), 'error')
                break
            except ValueError, exc:
                fail_count += 1
                self.pretty_print(exc, 'error')

        return fail_count

    def verify_py_pkgs(self, fail_count=0):
        fail_count += fail_count
        pkg_path = '{}{}'.format(self.amp_agent_path, self.amp_reqs_file)
        packages = []

        if not self.check_file(pkg_path):
            fail_count += 1
            self.pretty_print('Amplify agent requirements file was not found', 'error')
        else:
            packages = filter(None, self.read_file(pkg_path))

        rgx = '[^a-zA-Z0-9.]'

        for pkg in packages:
            try:
                required_pkg = sub(rgx, '', pkg)
                installed_pkgs = list(pkg_resources.find_distributions('%s/amplify' % self.amp_agent_path))
                installed_pkgs = [sub(rgx, '', str(package)) for package in installed_pkgs]

                if required_pkg not in installed_pkgs:
                    pkg_resources.require(pkg)

                if self.verbose:
                    self.pretty_print("The '{0}' distribution was found".format(pkg))
            except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict), exc:
                fail_count += 1
                self.pretty_print(exc, 'error')

        return fail_count

    def verify_all_packages(self):
        fail_count = 0

        fail_count = self.verify_sys_pkgs(fail_count)
        fail_count = self.verify_py_pkgs(fail_count)

        if fail_count is 0 and not self.verbose:
            self.pretty_print('All system and python packages are installed')

        return fail_count

    def verify_agent_ps(self):
        fail_count = 0

        if self.amp_pid is not None:
            self.pretty_print('Amplify agent is running...')
        else:
            fail_count += 1
            self.pretty_print('Amplify agent is NOT running...', 'error')

        return fail_count

    def verify_agent_log(self):
        fail_count = 0

        if self.check_file(self.amp_log_file):
            logs = self.read_file(self.amp_log_file)

            if len(logs) > 0:
                self.pretty_print('Amplify agent {0} file exists and is being updated'.format(self.file_name(self.amp_log_file)))
            else:
                fail_count += 1
                self.pretty_print('Amplify agent {0} file is NOT being updated'.format(self.file_name(self.amp_log_file)))
        else:
            fail_count += 1
            self.pretty_print('Amplify agent {0} file does NOT exist'.format(self.file_name(self.amp_log_file)), 'error')

        return fail_count

    def verify_agent_user(self):
        fail_count = 0

        if self.amp_owner is None:
            fail_count += 1
            self.pretty_print('Amplify agent user was not detected', 'error')
        elif self.amp_owner != self.ngx_worker_onwer:
            fail_count += 1
            self.pretty_print('{0} should run under [user: {1}]'
                              .format(self.amp_ps_name, self.ngx_worker_onwer), 'error')
        else:
            self.pretty_print('Amplify agent is running under the same user as NGINX worker processes [user: {0}]'
                              .format(self.amp_owner))

        return fail_count

    def verify_ngx_master_ps(self):
        fail_count = 0

        if self.ngx_pid is None:
            fail_count += 1
            self.pretty_print('NGINX is NOT running...', 'error')
        else:
            ngx_ppid = self.parent_pid(self.ngx_pid)
            path_absolute_status = os.path.isabs(self.ps_path(self.ngx_pid))

            if ngx_ppid != 1:
                fail_count += 1
                self.pretty_print('NGINX should start as a foreground system process', 'error')
            else:
                self.pretty_print('NGINX started as a foreground system process')

            if not path_absolute_status:
                fail_count += 1
                self.pretty_print('NGINX is not started with an absolute path.', 'error')
            else:
                self.pretty_print('NGINX is started with an absolute path')

        return fail_count

    def verify_sys_ps_access(self):
        fail_count = 0
        pid_list = self.check_ps_access()

        if self.ngx_pid is not None and int(self.ngx_pid) not in pid_list:
            fail_count += 1
            self.pretty_print('System user ID [{0}] CANNOT run ps(1) to see all system processes'
                              .format(self.current_user()), 'error')
        else:
            self.pretty_print('System user ID [{0}] can run ps(1) to see all system processes'.format(self.current_user()))

        return fail_count

    def verify_sys_time(self):
        fail_count = 0

        try:
            client = ntplib.NTPClient()
            res = client.request('pool.ntp.org').tx_time

            current_ntp_time = datetime.utcfromtimestamp(res)
            current_system_time = self.datetime_now()

            diff = abs(current_ntp_time - current_system_time)
            diff_in_secs = diff.days * 24 * 60 * 60 + diff.seconds

            if diff_in_secs > self.sys_time_diff_max_allowance:
                fail_count += 1
                self.pretty_print('System time is NOT set correctly. The time difference is: {0} seconds'
                                  .format(diff_in_secs), 'error')
            else:
                self.pretty_print('System time is set correctly')
        except (ntplib.NTPException, socket.gaierror), exc:
            fail_count += 1
            self.pretty_print('Cannot access NTP Server.', 'warn')

        return fail_count

    def verify_ngx_stub_status(self):
        fail_count = 0

        stub_status_file = self.check_file(self.ngx_status_conf_file)
        stub_status_filename = self.file_name(self.ngx_status_conf_file)
        ngx_conf_filename = self.file_name(self.ngx_conf_file)
        stub_status_module = 'http_stub_status_module'

        nginx_version = Popen(['nginx', '-V'], stderr=PIPE)
        nginx_trans = Popen(['tr', '--', '-', '\n'], stdin=nginx_version.stderr, stdout=PIPE)
        nginx_modules = Popen(['grep', '_module'], stdin=nginx_trans.stdout, stdout=PIPE)
        nginx_version.stderr.close()
        output, err = nginx_modules.communicate()

        nginx_modules = sub('\s+', ',', output.strip()).split(',')

        included_configs = []

        for block in self.ngx_conf_blocks:
            if block['directive'] == 'include':
                for arg in block['args']:
                    included_configs.append(arg.split('*')[0])

        if not stub_status_file:
            fail_count += 1
            self.pretty_print('NGINX {0} does not exist'.format(stub_status_filename), 'error')
        elif self.verbose:
            self.pretty_print('NGINX {0} is configured'.format(stub_status_filename))

        if self.ngx_status_conf_file.split(stub_status_filename)[0] not in included_configs:
            fail_count += 1
            self.pretty_print('NGINX {0} is NOT included in {1} file'
                              .format(stub_status_filename, ngx_conf_filename), 'error')
        elif self.verbose:
            self.pretty_print('NGINX {0} is included in {1} file'.format(stub_status_filename, ngx_conf_filename))

        if stub_status_module not in nginx_modules:
            fail_count += 1
            self.pretty_print('NGINX {0} is NOT included in the NGINX build'.format(stub_status_module), 'error')
        elif self.verbose:
            self.pretty_print('NGINX {0} is included in the NGINX build'.format(stub_status_module))

        if fail_count is 0 and not self.verbose:
            self.pretty_print('NGINX stub_status is configured and activated')

        return fail_count

    def verify_ngx_logs_read_access(self):
        fail_count = 0
        log_files = self.files(self.ngx_log_files)

        if len(log_files) > 0:
            for log_file in log_files:
                if self.file_owner(log_file) != self.ngx_worker_onwer or \
                        self.file_group(log_file) != self.ngx_owner or \
                        not self.check_file_read_perms(log_file):
                    fail_count += 1
                    self.pretty_print('NGINX {0} file is NOT readable by user {1}'
                                      .format(self.file_name(log_file), self.ngx_worker_onwer), 'error')
                elif self.verbose:
                    self.pretty_print('NGINX {0} file is readable by user {1}'
                                      .format(self.file_name(log_file), self.ngx_worker_onwer))
        else:
            fail_count += 1
            self.pretty_print('NGINX log files were not found', 'error')

        if fail_count is 0 and not self.verbose:
            self.pretty_print('NGINX log files are readable by user {0}'.format(self.ngx_worker_onwer))

        return fail_count

    def verify_ngx_config_files_access(self):
        fail_count = 0
        conf_files = self.dir_tree(self.ngx_all_confs_path)

        if len(conf_files) > 0:
            for conf_file in conf_files:
                if self.file_owner(conf_file) != self.amp_owner and \
                        self.file_group(conf_file) != self.amp_owner and \
                        not self.check_file_read_perms(conf_file):
                    fail_count += 1
                    self.pretty_print('NGINX {0} file is NOT readable by user {1}'
                                      .format(self.file_name(conf_file), self.amp_owner), 'error')
                elif self.verbose:
                    self.pretty_print('NGINX {0} file is readable by user {1}'
                                      .format(self.file_name(conf_file), self.amp_owner))
        else:
            fail_count += 1
            self.pretty_print('NGINX configuration files were not found', 'error')

        if fail_count is 0 and not self.verbose:
            self.pretty_print('NGINX configuration files are readable by user {0}'.format(self.amp_owner))

        return fail_count

    def verify_ngx_metrics(self):
        fail_count = 0
        current_metrics = []

        for block in self.ngx_conf_blocks:
            if block['directive'] == 'log_format':
                for args in block['args']:
                    for arg in args.split(' '):
                        current_metrics.append(arg.strip())

        if len(current_metrics) > 0:
            for metrics_arg in self.ngx_additional_metrics:
                if metrics_arg not in current_metrics:
                    fail_count += 1
                    self.pretty_print('NGINX [{0}] metrics argument is NOT applied on log_format directive in {1}'
                                      .format(metrics_arg, self.file_name(self.ngx_conf_file)), 'error')
                elif self.verbose:
                    self.pretty_print('NGINX [{0}] metrics argument is applied on log_format directive in {1}'
                                      .format(metrics_arg, self.file_name(self.ngx_conf_file)))
        else:
            fail_count += 1
            self.pretty_print('NGINX additional metrics are NOT applied on log_format directive in nginx.conf', 'error')

        if fail_count is 0 and not self.verbose:
            self.pretty_print('NGINX additional metrics are applied on log_format directive in {0}'
                              .format(self.file_name(self.ngx_conf_file)))

        return fail_count

    def verify_dns_resolver(self):
        "11. The system DNS resolver is correctly configured, and receiver.amplify.nginx.com can be successfully resolved."

    def verify_outbound_tls_access(self):
        fail_count = 0

        try:
            res = requests.get('https://receiver.amplify.nginx.com:443/ping')
            res.raise_for_status()

            self.pretty_print('Outbound TLS/SSL from the system to receiver.amplify.nginx.com is accessible')
        except requests.exceptions.RequestException, exc:
            fail_count += 1
            self.pretty_print(
                ['Outbound TLS/SSL from the system to receiver.amplify.nginx.com IS restricted', exc],
                'error'
            )

        return fail_count

    def verify_metrics_collection(self):
        "13. selinux(8), apparmor(7) or grsecurity are not interfering with the metric collection. E.g. for selinux(8) check /etc/selinux/config, try setenforce 0 temporarily and see if it improves the situation for certain metrics."

    def verify_proc_sys_access(self):
        "14. Some VPS providers use hardened Linux kernels that may restrict non-root users from accessing /proc and /sys. Metrics describing system and NGINX disk I/O are usually affected. There is no an easy workaround for this except for allowing the agent to run as root. Sometimes fixing permissions for /proc and /sys/block may work."
