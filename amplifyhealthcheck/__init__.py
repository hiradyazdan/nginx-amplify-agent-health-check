# -*- coding: utf-8 -*-

__author__ = "Hirad Yazdanpanah"
__license__ = "MIT"
__maintainer__ = "Hirad Yazdanpanah"

from healthcheck import AmplifyAgentHealthCheck

amplify_agent_path = '/opt/nginx-amplify-agent'
requirements_file = '/packages/nginx-amplify-agent/requirements'
amplify_conf_file = '/etc/amplify-agent/agent.conf'
amplify_log_file = '/var/log/amplify-agent/agent.log'
amplify_pid_file = '/var/run/amplify-agent/amplify-agent.pid'

nginx_all_confs_path = '/etc/nginx'
nginx_conf_file = '/etc/nginx/nginx.conf'
nginx_status_conf_file = '/etc/nginx/conf.d/stub_status.conf'
nginx_mime_types_file = '/etc/nginx/mime.types'
nginx_sites_available_conf_files = '/etc/nginx/sites-available/*.conf'
nginx_sites_enabled_conf_files = '/etc/nginx/sites-enabled/*.conf'
nginx_pid_file = '/var/run/nginx.pid'
nginx_log_files = '/var/log/nginx/*.log'


def configure(**attrs):
    return AmplifyAgentHealthCheck(
        verbose=attrs.get('verbose', False),
        decorate_mode=attrs.get('decorate_mode', True),
        heading=attrs.get('heading', 'Amplify Agent Health Check Analysis'),

        # Amplify
        amplify_agent_path=attrs.get('amplify_agent_path', amplify_agent_path),
        amplify_conf_file=attrs.get('amplify_conf_file', amplify_conf_file),
        amplify_log_file=attrs.get('amplify_log_file', amplify_log_file),
        amplify_pid_file=attrs.get('amplify_pid_file', amplify_pid_file),

        # Nginx
        nginx_all_confs_path=nginx_all_confs_path,
        nginx_conf_file=attrs.get('nginx_conf_file', nginx_conf_file),
        nginx_status_conf_file=attrs.get('nginx_status_conf_file', nginx_status_conf_file),
        nginx_sites_available_conf_files=attrs.get('nginx_sites_available_conf_files', nginx_sites_available_conf_files),
        nginx_sites_enabled_conf_files=attrs.get('nginx_sites_enabled_conf_files', nginx_sites_enabled_conf_files),
        nginx_mime_types_file=attrs.get('nginx_mime_types_file', nginx_mime_types_file),
        nginx_log_files=attrs.get('nginx_log_files', nginx_log_files),
        nginx_pid_file=attrs.get('nginx_pid_file', nginx_pid_file),

        # System
        max_time_diff_allowance=attrs.get('max_time_diff_allowance', 80)
    ).configure().generate_output()
