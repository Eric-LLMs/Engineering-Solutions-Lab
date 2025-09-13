#!/bin/bash
# 启动服务脚本，主要用于本地开发
# ./startup.sh [template]
#   template: 启动模板

set -e
set -x
__base__=$(readlink -f $(dirname $(readlink -f $0))/..)
__bin__=${__base__}/bin
__conf__=${__base__}/conf
__interface__=${__base__}/interfaces

# 动态配置模板
if [ $# -gt 0 ]; then
    template=$1
else
    template=${__conf__}/templates/local.yml
fi

# 生成 etcd-proxy 配置
python3 ${__bin__}/generate-config.py -t ${template} -r ${__conf__} -e etcd.yml.j2

# 编译接口
make -C ${__interface__}

# 启动app
python3 ${__bin__}/app.py
