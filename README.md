# NGINX Amplify Agent Health Check

[![PyPI version](https://img.shields.io/pypi/v/nginx-amplify-agent-health-check.svg)](https://pypi.org/project/nginx-amplify-agent-health-check)
[![Python versions](https://img.shields.io/pypi/pyversions/nginx-amplify-agent-health-check.svg)](https://pypi.org/project/nginx-amplify-agent-health-check)
[![License](https://img.shields.io/pypi/l/nginx-amplify-agent-health-check.svg)](https://github.com/hiradyazdan/nginx-amplify-agent-health-check/blob/master/LICENSE.txt)

[![CircleCI](https://circleci.com/gh/hiradyazdan/nginx-amplify-agent-health-check.svg?style=shield&circle-token=592d09559d8a59748ff9d1870a83cb5eb9cc621c)](https://circleci.com/gh/hiradyazdan/nginx-amplify-agent-health-check)
[![Coverage Status](https://coveralls.io/repos/github/hiradyazdan/nginx-amplify-agent-health-check/badge.svg?branch=master)](https://coveralls.io/github/hiradyazdan/nginx-amplify-agent-health-check?branch=master)
[![Code Health](https://landscape.io/github/hiradyazdan/nginx-amplify-agent-health-check/master/landscape.svg?style=flat&badge_auth_token=49645f59a46e447e823775fa30645d54)](https://landscape.io/github/hiradyazdan/nginx-amplify-agent-health-check/master)
[![Requirements Status](https://requires.io/github/hiradyazdan/nginx-amplify-agent-health-check/requirements.svg?branch=master)](https://requires.io/github/hiradyazdan/nginx-amplify-agent-health-check/requirements/?branch=master)

## Setup

```shell
pip install nginx-amplify-agent-health-check
```

## Usage

#### via Command Line:

```shell
amphc
```

#### via the API:

```python
import amplifyhealthcheck as amphc

amplify_agent_path = '/opt/nginx-amplify-agent'
amplify_reqs_file = '/packages/nginx-amplify-agent/requirements'
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

amphc = amphc.configure(
    verbose=False,
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

amphc.verify_agent_ps()
amphc.verify_agent_log()
amphc.verify_agent_user()

amphc.verify_ngx_master_ps()
amphc.verify_ngx_stub_status()
amphc.verify_ngx_logs_read_access()
amphc.verify_ngx_config_files_access()
amphc.verify_ngx_metrics()

amphc.verify_all_packages()
amphc.verify_sys_time()
amphc.verify_sys_ps_access()
amphc.verify_outbound_tls_access()
amphc.verify_proc_sys_access()
amphc.verify_dns_resolver()
amphc.verify_metrics_collection()
```