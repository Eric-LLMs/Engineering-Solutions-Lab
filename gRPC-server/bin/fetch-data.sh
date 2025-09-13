#!/bin/bash
# 从数据中心拉取数据部署环境
# 依赖ansible，请确保使用python3安装ansible包

set -e
set -x

__base__=$(readlink -f $(dirname $(readlink -f $0))/..)
__conf__=${__base__}/conf
__ita__=${__base__}/ita
__build__=${__base__}/build

if [ $# -gt 0 ]; then
    template=$1
else
    template=${__conf__}/templates/local.yml
fi

# git clone build
if [[ ! -d ${__build__} ]]; then
    git clone git@192.168.1.78:model-services/live-comments-analysis-build.git ${__build__}
    cd ${__build__}
else
    cd ${__build__}
    git pull
fi
# git clone ita
if [[ ! -d ${__ita__} ]]; then
    git clone git@192.168.1.78:algorithms/ita2.git ${__ita__}
    cd ${__ita__}
else
    cd ${__ita__}
    git pull
fi

ansible-playbook ../build/playbooks/fetch-data.yml -e dict_destination="${__base__}/data" -e @${template} -e datacenter_name=datacenter_intranet -e cluster_name=staging
