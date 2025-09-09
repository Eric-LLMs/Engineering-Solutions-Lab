#!/bin/bash
# 启动服务

set -e
set -x

__base__=$(readlink -f $(dirname $(readlink -f $0))/..)
__bin__=${__base__}/bin
__conf__=${__base__}/conf

# 动态配置模板
if [ $# -gt 0 ]; then
    template=$1
else
    template=${__conf__}/templates/local.yml
fi

# 编译接口
make -C app/interfaces

# 生成配置
python3 ${__bin__}/generate-config.py -d ${template} -r ${__conf__} -e etcd.yml.j2

# 获取参数
THREAD_NUM=$(grep -P '^thread_num' ${__conf__}/service.yml | tr -d ' \n\r' | awk -F':' '{print $NF}')
LISTEN_PORT=$(grep -P '^listen_port' ${__conf__}/service.yml | tr -d ' \n\r' | awk -F':' '{print $NF}')

# 运行
uvicorn --host 0.0.0.0 --port ${LISTEN_PORT} --workers ${THREAD_NUM} app:app
