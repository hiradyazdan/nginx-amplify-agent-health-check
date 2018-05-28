# -*- coding: utf-8 -*-

__author__ = "Hirad Yazdanpanah"
__license__ = "MIT"
__maintainer__ = "Hirad Yazdanpanah"

import io
import sys
import ast
import ConfigParser

from base import Base
from healthcheck import AmplifyAgentHealthCheck


def configure(**attrs):
    amphc = init(**attrs).configure().generate_output()

    return amphc


def init(**attrs):
    config_file = './config.ini'
    custom_config_file = attrs.get('config_file', '')

    try:
        with open(config_file) as f:
            config_stream = f.read()

        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.readfp(io.BytesIO(config_stream))

        if custom_config_file:
            with open(custom_config_file, 'r') as f:
                config_stream = f.read()

            config.readfp(io.BytesIO(config_stream))
    except (ConfigParser.MissingSectionHeaderError, IOError), exc:
        Base().pretty_print(exc, 'error', False)
        sys.exit()

    amphc = AmplifyAgentHealthCheck(
        verbose=attrs.get('verbose', False),
        decorate_mode=attrs.get('decorate_mode', True),
        heading=config.get('options', 'heading'),

        # Amplify
        amplify_agent_path=config.get('options', 'amplify_agent_path'),
        amplify_reqs_file=config.get('options', 'amplify_reqs_file'),
        amplify_conf_file=config.get('options', 'amplify_conf_file'),
        amplify_log_file=config.get('options', 'amplify_log_file'),
        amplify_pid_file=config.get('options', 'amplify_pid_file'),

        # Nginx
        nginx_all_confs_path=config.get('options', 'nginx_all_confs_path'),
        nginx_conf_file=config.get('options', 'nginx_conf_file'),
        nginx_status_conf_file=config.get('options', 'nginx_status_conf_file'),
        nginx_sites_available_conf_files=config.get('options', 'nginx_sites_available_conf_files'),
        nginx_sites_enabled_conf_files=config.get('options', 'nginx_sites_enabled_conf_files'),
        nginx_mime_types_file=config.get('options', 'nginx_mime_types_file'),
        nginx_log_files=config.get('options', 'nginx_log_files'),
        nginx_pid_file=config.get('options', 'nginx_pid_file'),
        nginx_additional_metrics=ast.literal_eval(config.get('options', 'nginx_additional_metrics')),

        # System
        system_packages=ast.literal_eval(config.get('options', 'system_packages')),
        system_find_package_command=ast.literal_eval(config.get('options', 'system_find_package_command')),
        system_time_diff_max_allowance=config.get('options', 'system_time_diff_max_allowance')
    )

    return amphc
