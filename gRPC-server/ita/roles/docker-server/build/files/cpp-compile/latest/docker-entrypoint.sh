#!/bin/bash
# docker container entrypoint script

set -x
set -e
set -o pipefail

# 调用编译脚本
/bin/bash /root/make.sh
