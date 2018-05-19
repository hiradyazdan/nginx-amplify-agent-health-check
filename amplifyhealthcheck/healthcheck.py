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

        # Amplify
        self.amp_agent_path = attrs['amplify_agent_path']
        self.amp_conf_file = attrs['amplify_conf_file']
        self.amp_log_file = attrs['amplify_log_file']
        self.amp_pid_file = attrs['amplify_pid_file']

        # Nginx
        self.ngx_all_confs_path = attrs['nginx_all_confs_path']
        self.ngx_conf_file = attrs['nginx_conf_file']
        self.ngx_status_conf_file = attrs['nginx_status_conf_file']
        self.ngx_sites_available_conf_files = attrs['nginx_sites_available_conf_files']
        self.ngx_sites_enabled_conf_files = attrs['nginx_sites_enabled_conf_files']
        self.ngx_mime_types_file = attrs['nginx_mime_types_file']
        self.ngx_log_files = attrs['nginx_log_files']
        self.ngx_pid_file = attrs['nginx_pid_file']

        # System
        self.max_time_diff_allowance = attrs['max_time_diff_allowance']

        self.ngx_worker_onwer = None
        self.ngx_worker_pid = None

        self.amp_pid = self.read_file(self.amp_pid_file)[0]
        self.amp_owner = self.ps_owner(self.amp_pid)
        self.amp_ps_name = self.ps_name(self.amp_pid)
        self.ngx_pid = self.read_file(self.ngx_pid_file)[0]
        self.ngx_owner = self.ps_owner(self.ngx_pid)

    def generate_output(self):
        print '\n----- {0}{1}{2} -----\n'.format(self.cyan_color, self.heading, self.no_color)

        atexit.register(self.decorate)

        return self

    def verify_sys_pkgs(self, packages, find_sys_pkg_cmd, fail_count):
        for pkg in packages:
            try:
                status = call(find_sys_pkg_cmd + [pkg], stdout=devnull, stderr=devnull)

                if status != 0:
                    raise ValueError('{0} package {1} was NOT found'.format(find_sys_pkg_cmd[0], pkg))
                elif self.verbose:
                    self.pretty_print('{0} package {1} was found'.format(find_sys_pkg_cmd[0], pkg))
            except ValueError, exc:
                fail_count += 1
                self.pretty_print(exc, 'error')

    def verify_py_pkgs(self, packages, fail_count):
        rgx = '[^a-zA-Z0-9.]'

        for pkg in packages:
            try:
                dep_match = sub(rgx, '', pkg)
                py_pkgs = list(pkg_resources.find_distributions('%s/amplify' % self.amp_agent_path))
                py_pkgs = [sub(rgx, '', str(package)) for package in py_pkgs]

                if dep_match not in py_pkgs:
                    pkg_resources.require(pkg)

                if self.verbose:
                    self.pretty_print("The '{0}' distribution was found".format(pkg))
            except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict), exc:
                fail_count += 1
                self.pretty_print(exc, 'error')

    def verify_all_packages(self, packages, requirements_file, find_sys_pkg_cmd):
        fail_count = 0
        deps_path = '{0}{1}'.format(self.amp_agent_path, requirements_file)
        required_deps = filter(None, self.read_file(deps_path))

        self.verify_sys_pkgs(packages, find_sys_pkg_cmd, fail_count)
        self.verify_py_pkgs(required_deps, fail_count)

        if fail_count is 0 and not self.verbose:
            self.pretty_print('All system and python packages are installed')

    def verify_agent_ps(self):
        pid_file = self.check_file(self.amp_pid_file)

        if pid_file:
            self.pretty_print('Amplify agent is running...')
        else:
            self.pretty_print('Amplify agent is NOT running...', 'error')

    def verify_agent_log(self):
        log_file = self.check_file(self.amp_log_file)
        logs = self.read_file(self.amp_log_file)

        if log_file and logs > 0:
            self.pretty_print('Amplify {0} file exists and is being updated'.format(self.file_name(self.amp_log_file)))
        elif not log_file:
            self.pretty_print('Amplify {0} file does NOT exist'.format(self.file_name(self.amp_log_file)), 'error')
        else:
            self.pretty_print('Amplify {0} file is NOT being updated'
                              .format(self.file_name(self.amp_log_file)), 'error')

    def verify_agent_user(self):
        self.ngx_worker_pid = self.pid('nginx: worker process')[0]
        self.ngx_worker_onwer = self.ps_owner(self.ngx_worker_pid)

        if self.amp_owner != self.ngx_worker_onwer:
            self.pretty_print('{0} should run under [user: {1}]'
                              .format(self.amp_ps_name, self.ngx_worker_onwer), 'error')
        else:
            self.pretty_print('Amplify agent is running under the same user as NGINX worker processes [user: {0}]'
                              .format(self.amp_owner))

    def verify_ngx_start_path(self):
        path_absolute_status = os.path.isabs(self.ps_path(self.ngx_pid))

        if not path_absolute_status:
            self.pretty_print('NGINX is not started with an absolute path.', 'error')
        else:
            self.pretty_print('NGINX is started with an absolute path')

    def verify_sys_ps_access(self):
        pid_list = self.check_ps_access()

        if int(self.ngx_pid) not in pid_list:
            self.pretty_print('The user ID [{0}] CANNOT run ps(1) to see all system processes'
                              .format(self.current_user()), 'error')
        else:
            self.pretty_print('The user ID [{0}] can run ps(1) to see all system processes'.format(self.current_user()))

    def verify_sys_time(self):
        try:
            client = ntplib.NTPClient()
            res = client.request('pool.ntp.org').tx_time

            current_ntp_time = datetime.utcfromtimestamp(res)
            current_system_time = datetime.now()

            diff = abs(current_ntp_time - current_system_time)
            diff_in_secs = diff.days * 24 * 60 * 60 + diff.seconds

            if diff_in_secs > self.max_time_diff_allowance:
                self.pretty_print('The system time is NOT set correctly. The time difference is: {0} seconds'
                                  .format(diff_in_secs), 'error')
            else:
                self.pretty_print('The system time is set correctly')
        except (ntplib.NTPException, socket.gaierror), exc:
            self.pretty_print('Cannot access NTP Server.', 'warn')

    def verify_ngx_stub_status(self):
        fail_count = 0

        stub_status_file = self.check_file(self.ngx_status_conf_file)
        stub_status_filename = self.file_name(self.ngx_status_conf_file)
        stub_status_module = 'http_stub_status_module'

        nginx_version = Popen(['nginx', '-V'], stderr=PIPE)  # No idea why nginx -V redirects output to stderr
        nginx_trans = Popen(['tr', '--', '-', '\n'], stdin=nginx_version.stderr, stdout=PIPE)
        nginx_modules = Popen(['grep', '_module'], stdin=nginx_trans.stdout, stdout=PIPE)
        nginx_version.stderr.close()
        output, err = nginx_modules.communicate()

        nginx_modules = sub('\s+', ',', output.strip()).split(',')

        if not stub_status_file:
            fail_count += 1
            self.pretty_print('{0} does not exist'.format(stub_status_filename), 'error')
        elif self.verbose:
            self.pretty_print('{0} is configured'.format(stub_status_filename))

        if stub_status_module not in nginx_modules:
            fail_count += 1
            self.pretty_print('{0} is NOT included in the NGINX build'.format(stub_status_module), 'error')
        elif self.verbose:
            self.pretty_print('{0} is included in the NGINX build'.format(stub_status_module))

        if fail_count is 0 and not self.verbose:
            self.pretty_print('NGINX stub status is configured and activated')

    def verify_ngx_logs_read_access(self):
        fail_count = 0
        log_files = self.files(self.ngx_log_files)

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

        if fail_count is 0 and not self.verbose:
            self.pretty_print('NGINX log files are readable by user {0}'.format(self.ngx_worker_onwer))

    def verify_ngx_config_files_access(self):
        fail_count = 0
        conf_files = self.dir_tree(self.ngx_all_confs_path)

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

        if fail_count is 0 and not self.verbose:
            self.pretty_print('NGINX configuration files are readable by user {0}'.format(self.amp_owner))

    def verify_ngx_metrics(self, required_metrics):
        fail_count = 0
        conf = crossplane.parse(self.ngx_conf_file)
        current_metrics = []

        for config in conf['config']:
            for parsed in config.get('parsed', []):
                for block in parsed.get('block', []):
                    if block['directive'] == 'log_format':
                        for args in block['args']:
                            for arg in args.split(' '):
                                current_metrics.append(arg.strip())

        for metrics_arg in required_metrics:
            if metrics_arg not in current_metrics:
                fail_count += 1
                self.pretty_print('NGINX [{0}] metrics argument is NOT applied on log_format directive in {1}'
                                  .format(metrics_arg, self.file_name(self.ngx_conf_file)), 'error')
            elif self.verbose:
                self.pretty_print('NGINX [{0}] metrics argument is applied on log_format directive in {1}'
                                  .format(metrics_arg, self.file_name(self.ngx_conf_file)))

        if fail_count is 0 and not self.verbose:
            self.pretty_print('NGINX additional metrics are applied on log_format directive in {0}'
                              .format(self.file_name(self.ngx_conf_file)))

    def verify_dns_resolver(self):
        "11. The system DNS resolver is correctly configured, and receiver.amplify.nginx.com can be successfully resolved."

    def verify_outbound_tls_access(self):
        try:
            requests.get('https://receiver.amplify.nginx.com')
            self.pretty_print('Oubound TLS/SSL from the system to receiver.amplify.nginx.com is not restricted')
        except requests.exceptions.ConnectionError, exc:
            self.pretty_print('Oubound TLS/SSL from the system to receiver.amplify.nginx.com IS restricted', 'error')

    def verify_metrics_collection(self):
        "13. selinux(8), apparmor(7) or grsecurity are not interfering with the metric collection. E.g. for selinux(8) check /etc/selinux/config, try setenforce 0 temporarily and see if it improves the situation for certain metrics."

    def verify_proc_sys_access(self):
        "14. Some VPS providers use hardened Linux kernels that may restrict non-root users from accessing /proc and /sys. Metrics describing system and NGINX disk I/O are usually affected. There is no an easy workaround for this except for allowing the agent to run as root. Sometimes fixing permissions for /proc and /sys/block may work."
        self.amp_owner
