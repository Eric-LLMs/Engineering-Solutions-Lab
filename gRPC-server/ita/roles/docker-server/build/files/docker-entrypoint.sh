#!/bin/bash
# docker container entrypoint script

set -x
set -e
set -o pipefail

exec /usr/sbin/init
/sbin/sshd -D
