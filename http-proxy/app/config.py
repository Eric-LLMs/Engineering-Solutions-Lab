# application config

import logging
from pathlib import Path
import yaml
from pydantic import BaseModel
from typing import Union, Dict, List, Any


class SchedulerConfig(BaseModel):
    '''调度器配置'''
    impl: str   # 调度器实现类
    args: Dict[str, Any]    # 调度器服务参数


class AppConfig(BaseModel):
    '''fastapi application配置'''
    thread_num: int  # 工作线程数

    docs_url: Union[str, None] = '/docs'
    openapi_url: Union[str, None] = '/openapi.json'
    redoc_url: Union[str, None] = '/redoc'

    dynamics: Dict[str, Any]    # 服务动态配置
    schedulers: Dict[str, SchedulerConfig]  # 后端调度器配置
    tables: List[Dict]  # 表配置


# service.yml
SERVICE_CONF_FILENAME = Path('conf/service.yml')

# tables.yml
TABLES_CONF_FILENAME = Path('conf/tables.yml')


def fill_fs_relation(conf: dict) -> bool:
    '''
    @brief 填充表结构间的父子关系
    @param[in/out] conf: 表字典，顶层追加'father'的key,
            like: father: {name:xxx, [fkey:xxx, skey:xxx], name:yyy, [fkey:yyy, skey:yyy]}
    @return True: 成功  False: 失败
    '''
    try:
        for table in conf['tables']:
            # 表配置增加father关系节点，方便查询
            father_tables = {}
            for subtable in table['subtables']:
                cur_table_name = subtable['name']
                for key in subtable['keys']:
                    cur_key_name = key['name']
                    if 'foreign_tables' not in key:
                        continue
                    for foreign_table in key['foreign_tables']:
                        f_table_name = foreign_table['name']
                        if 'forkey' in foreign_table:
                            fkey = foreign_table['forkey']
                        father_info = {}
                        father_info['fkey'] = cur_key_name      # 父表键名
                        if 'forkey' in foreign_table:
                            # 自身键名
                            father_info['skey'] = foreign_table['forkey']
                        if 'scope' in foreign_table:
                            father_info['scope'] = foreign_table['scope']
                        if 'keep_relationship' in foreign_table:
                            father_info['keep_relationship'] = foreign_table['keep_relationship']
                        father_info['pos'] = 0
                        if f_table_name not in father_tables:
                            father_tables[f_table_name] = {}
                        if cur_table_name not in father_tables[f_table_name]:
                            father_tables[f_table_name][cur_table_name] = []
                        father_tables[f_table_name][cur_table_name].append(
                            father_info)
            for subtable in table['subtables']:
                if subtable['name'] in father_tables:
                    if 'father' not in subtable:
                        subtable['father'] = {}
                    subtable['father'] = father_tables[subtable['name']]

        # 表顺序重排，按照父子层级关系先后排序
        for table in conf['tables']:
            sorted_table_name = set()
            sorted_table_list = []
            resorted_table_list = []
            while(len(sorted_table_list) != len(table['subtables'])):
                begin_len = len(sorted_table_list)
                for subtable in table['subtables']:
                    if subtable['name'] in sorted_table_name:
                        continue
                    if 'father' not in subtable:
                        sorted_table_name.add(subtable['name'])
                        sorted_table_list.append(subtable['name'])
                        resorted_table_list.append(subtable)
                        continue
                    else:
                        flag = True
                        for father_table_name in subtable['father'].keys():
                            if father_table_name not in sorted_table_name and father_table_name != subtable['name']:
                                flag = False
                        if flag:
                            sorted_table_name.add(subtable['name'])
                            sorted_table_list.append(subtable['name'])
                            resorted_table_list.append(subtable)
                end_len = len(sorted_table_list)
                if begin_len == end_len:
                    logging.warn(
                        "resort table list failed!please check the table config!")
                    return False
            table['subtables'] = resorted_table_list
    except:
        print('fill_fs_relation call failed')
        return False

    return True


def loadServiceConfig():
    '''
    载入服务配置
    @return 配置数据
    '''
    try:
        with SERVICE_CONF_FILENAME.open('rt') as f:
            data = yaml.safe_load(f)
        with TABLES_CONF_FILENAME.open('rt') as f:
            tables = yaml.safe_load(f)
            if not fill_fs_relation(tables):
                raise ('fill_fs_relation call failed!')
        data = dict(data, **tables)
        config = AppConfig(**data)
        return config
    except Exception as ex:
        logging.critical('failed to load service config {}: {}'.format(
            SERVICE_CONF_FILENAME, ex))
        raise ex
