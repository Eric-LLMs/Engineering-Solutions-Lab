#!/usr/bin/env python3
# coding=utf-8
# 设置/etc/docker/daemon.json
# 如果返回 0，表示没有改动，1 表示有改动，-1 表示异常

import json
import os
import sys

try:
    data = {}

    if os.path.isfile('/etc/docker/daemon.json'):
        with open('/etc/docker/daemon.json', 'r') as fh:
            try:
                data = json.load(fh)
            except:
                print('failed to load daemon.json', file=sys.stderr)

    # 设置配置
    modified = False
    # 加入docker中国镜像
    if 'registry-mirrors' not in data:
        data['registry-mirrors'] = []
        modified = True

    for url in [
        'https://9cpn8tt6.mirror.acmecs.com'
    ]:
        if url not in data['registry-mirrors']:
            data['registry-mirrors'].append(url)
            modified = True
    data['registry-mirrors'] = list(set(data['registry-mirrors']))

    # 加入公司私有docker registry
    if 'insecure-registries' not in data:
        data['insecure-registries'] = []
        modified = True

    for url in [
        '192.168.1.128',
        'harbor. acme.com',
    ]:
        if url not in data['insecure-registries']:
            data['insecure-registries'].append(url)
            modified = True
    data['insecure-registries'] = list(set(data['insecure-registries']))

    if not os.path.exists('/etc/docker'):
        os.makedirs('/etc/docker')
    with open('/etc/docker/daemon.json', 'w') as fh:
        print(json.dumps(data, indent=4, ensure_ascii=True, sort_keys=True), file=fh)
except:
    import traceback

    traceback.print_exc()

    # 发生异常，返回 -1
    sys.exit(-1)
else:
    if modified:
        sys.exit(1)
