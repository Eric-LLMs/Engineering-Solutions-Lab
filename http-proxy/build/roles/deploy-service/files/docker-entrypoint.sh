#!/bin/bash
# docker container entrypoint script

set -x
set -e
set -o pipefail

export LANG="en_US.UTF-8"
# 启动服务
supervisord -c /root/supervisor/supervisord.conf

/sbin/sshd -D
