#!/bin/bash
# docker container entrypoint script

set -x
set -e
set -o pipefail

/sbin/sshd -D
