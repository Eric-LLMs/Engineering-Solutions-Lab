'''
@brief 构建患者管理建库doc。
@author  
@email  @acme.cn
@date 2020.06.29
@update 2020.06.29
'''

import json
import logging
import time
import datetime
import copy
import traceback
import numpy as np

from app import app
from app.scheduler import requestScheduler


class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return json.JSONEncoder.default(self, obj)


class DataBuilder:
    def __init__(self, doctype, docname, tables):
        '''
        @brief 构造函数
        @param[in] doctype: 文档类型
        @param[in] docname: 类型名称
        @param[in] tables: 配置表
        '''
        self.doctype = doctype
        self.docname = docname
        self.tables = tables
        self.docid_list = []
        return

    def __get_id(self, index):
        while (len(self.docid_list) <= index):
            self.docid_list.append(0)
        self.docid_list[index] = self.docid_list[index] + 1
        return self.docid_list[index]

    def __bebuild(self, key):
        if (self.doctype == 8):
            if key == 'name' or key == 'disease_name' or \
               key == 'disease_alias' or key == 'operation_name' or \
               key == 'folder_id' or key == 'tag_name':
                return True
        else:
            return False

    def __beseg(self, key):
        ret = self.__bebuild(key)
        if (self.doctype == 8):
            if key == 'folder_id':
                return False
        return ret

    def __find_last_text_contents_index(self, doc) -> str:
        max_index = 0
        for segment in doc['segments']:
            if len(segment['id']) >= 13 and segment['id'][0:13] == 'text_contents':
                segid = segment['id']
                segid = segid[13:len(segid)]
                segid = segid.rstrip(']')
                segid = segid.lstrip('[')
                if (int(segid) > max_index):
                    max_index = int(segid)
        return 'text_contents' + '[' + str(max_index + 1) + ']'

    def __add_segment(self, isbuild, isseg, isfilter, granularity, seg_id, seg_text, doc):
        # 判断seg_id是否已在doc中，若在doc中，则通过‘换行+seg_text’的方式追加
        if 'segments' in doc:
            for segment in doc['segments']:
                if segment['id'] == seg_id:
                    # trick逻辑，当发现某些指id存在多个时，continue
                    sprets = seg_id.split('.')
                    if len(sprets) >= 5 and sprets[4] == 'name':
                        continue
                    if len(seg_id) >= 13 and seg_id[0:13] == 'text_contents':
                        segment['id'] = self.__find_last_text_contents_index(
                            doc)
                        break
                    segment['text'] = segment['text'] + '\n' + seg_text
                    segment['offsegnum'] = len(str(segment['text']).encode())
                    return

        # 不存在则添加
        segment = {}
        segment['id'] = seg_id
        if seg_text == None:
            segment['text'] = ""
        else:
            segment['text'] = str(seg_text)
        segment['textlen'] = len(str(segment['text']).encode())
        segment['codetype'] = 'utf8'

        segment['offsegnum'] = 0
        segment['bebuilt'] = 0
        if isbuild:
            segment['offsegnum'] = len(str(segment['text']).encode())
            segment['bebuilt'] = 1
            '''
            if(len(segment['text']) <= 0):
                return
            '''
            if self.max_text_len < segment['textlen']:
                self.max_text_len = segment['textlen']

        segment['isseg'] = 0
        if isseg:
            segment['isseg'] = 1

        segment['isfilter'] = isfilter
        segment['granularity'] = granularity
        segment['isshow'] = 1
        segment['weight'] = 100
        doc['segnum'] += 1
        doc['segments'].append(segment)

    def __build_prefix_name(self, table_name: str, index: int, clean_result: dict) -> str:
        '''
        @brief 构建目标名前缀
        @param[in] table_name: 表名
        @param[index]: index: 索引号
        @param[in] clean_results: clean结果
        @return 构建好的字符串
        '''
        result_item = clean_result[table_name][index]
        if '__relation__' not in result_item or len(result_item['__relation__']) <= 0:
            return ''

        father_table_name = list(result_item['__relation__'].keys())[0]
        father_table_index = list(result_item['__relation__'].values())[0]
        real_index = result_item['__index__']

        father_prefix = self.__build_prefix_name(
            father_table_name, father_table_index, clean_result)

        if 'tarname' in self.tables[table_name]:
            if len('tarname') > 0:
                return ''.join('%s%s[%d].' % (father_prefix, self.tables[table_name]['tarname'], real_index))
            else:
                return ''.join('%s' % (father_prefix))
        else:
            return father_prefix

    # 患者管理
    def __build_patient_manager(self, prikey: str, clean_results: list, build_results: list):
        '''构建患者管理建库文件
        @param[in] clean_results  清洗后的数据数组
        @param[out] build_results 返回建库结果
        '''
        self.docid = 0
        self.linecount = 0
        self.max_text_len = 0

        for clean_result in clean_results:
            self.linecount += 1
            doc = {}
            doc['typeid'] = 8
            doc['segnum'] = 0
            doc['docid'] = prikey
            doc['timestamp'] = self.pull_table_time
            doc['segments'] = []

            if len(list(clean_result.values())[0]) <= 0:
                build_results.append(doc)
                return

            # 构建source 和 doc_weight
            self.__add_segment(self.__bebuild("SOURCE"), self.__beseg(
                "SOURCE"), 0, 2, "SOURCE", "acme-patient", doc)
            score = 100
            self.__add_segment(self.__bebuild("WEIGHT"), self.__beseg(
                "WEIGHT"), 0, 2, "WEIGHT", str(score), doc)

            for (table_name, data_items) in clean_result.items():
                keys = self.tables[table_name]['keys']
                for (idx, data_item) in enumerate(data_items):
                    cur_prefix = self.__build_prefix_name(
                        table_name, idx, clean_result)
                    for (k, v) in data_item.items():
                        dst_name = ''
                        if v is None or k == '__relation__' or k == '__index__':
                            continue
                        v = str(v)
                        beindex = False
                        bebuild = True
                        beseg = True
                        granularity = 2
                        isfilter = 0
                        dst_name = cur_prefix + k
                        if 'beindex' in keys[k]:
                            beindex = keys[k]['beindex']
                        if 'bebuild' in keys[k]:
                            bebuild = keys[k]['bebuild']
                        if not bebuild:
                            continue
                        if 'beseg' in keys[k]:
                            beseg = keys[k]['beseg']
                        if 'granularity' in keys[k]:
                            granularity = keys[k]['granularity']
                        if 'isfilter' in keys[k]:
                            isfilter = keys[k]['isfilter']
                        if 'tarname' in keys[k]:
                            dst_name = cur_prefix + keys[k]['tarname']
                            dst_name = dst_name.strip()
                        if 'islist' in keys[k] and keys[k]['islist']:
                            dst_name = dst_name + "[" + str(idx) + "]"
                        dst_name = dst_name.rstrip('.')

                        self.__add_segment(
                            beindex, beseg, isfilter, granularity, dst_name, v, doc)
                        if k == 'name' and table_name == 'patient':
                            self.__add_segment(
                                False, True, 0, 2, 'TITLE', v, doc)
            self.__add_segment(False, False, 0, 2, 'DOCID', prikey, doc)
            self.__add_segment(False, False, 0, 2,
                               'TIMESTAMP', doc['timestamp'], doc)
            build_results.append(doc)

        app.logger.debug("最大文本长度:%d" % self.max_text_len)
        app.logger.debug("segment个数:%d" % (len(doc['segments'])))

    def __check_need_correct(self, id: str) -> str:
        '''
        @brief 检查是否当前key需要后处理
        @return 返回需要校验的字符串
        '''
        split_ret = id.split('.')
        if len(split_ret) == 5:
            if split_ret[4][0:5] == 'value':
                ret_str = split_ret[0] + '.' + split_ret[1] + '.' + \
                    split_ret[2] + '.' + split_ret[3] + '.' + 'name'
                return ret_str
        return ''

    def __correct_result(self, key_name: str) -> bool:
        '''
        @brief 检查是否当前key需要后处理
        '''
        if key_name == '主诉' or \
                key_name == '症状' or \
                key_name == '假体名称' or \
                key_name == '手术工具名称':
            return True

        return False

    def __find_result(self, key_name: str, segments: list) -> int:
        '''
        @brief 根据id查找segments, 返回pos位置
        '''
        for (idx, segment) in enumerate(segments):
            if segment['id'] == key_name:
                return idx

        return -1

    def __postprocess(self, build_results: list) -> None:
        '''
        @brief 建库数据后处理
        @param[in/out] build_results
            需要处理的建库数据
        '''

        for build_result in build_results[:]:
            unmatch_prefix_list = []
            for segment in build_result['segments'][:]:
                bebuilt = segment['bebuilt']
                if bebuilt != 1:
                    continue
                check_str = self.__check_need_correct(segment['id'])
                if len(check_str) <= 0:
                    continue
                pos = self.__find_result(check_str, build_result['segments'])
                if pos < 0:
                    logging.warn(
                        'The appropriate itemName was not matched[%s]' % (check_str))
                    unmatch_prefix_list.append(check_str[0:len(check_str) - 5])
                    continue
                    raise Exception(
                        'The appropriate itemName was not matched[%s]' % (check_str))
                if not self.__correct_result(build_result['segments'][pos]['text']):
                    segment['bebuilt'] = 0
            '''
            for prefix in unmatch_prefix_list:
                #清理不匹配数据【用来trick某些点位名找不到的情况】
                prefix_len = len(prefix)
                for segment in build_result['segments'][:]:
                    if len(segment['id']) <= prefix_len:
                        continue
                    id_prefix = segment['id'][0:(prefix_len)]
                    if id_prefix != prefix:
                        continue
                    build_result['segments'].remove(segment)
            '''

    def do_build(self, pull_table_time, prikey, clean_results, build_results):
        self.pull_table_time = pull_table_time
        if (self.doctype == 8):
            self.__build_patient_manager(prikey, clean_results, build_results)
            self.__postprocess(build_results)
        else:
            logging.fatal("no relevate doctype")
            return False

        return True


class DataLoader:
    def __init__(self):
        pass

    def do_search(self, dbname: str, dbsource: str, table_name: str, search_condition: dict, results: dict) -> bool:
        '''
        @brief 查询表
        @param[in] dbname: db名称
        @param[in] dbsource: db来源 [mysql][mongo]
        @param[in] table_name: 表名称
        @param[in] search_condition: 查询条件
                like
            {'patient_id':'eb25483fff564d2eb927822a429991cd','disease_course_id':'668216f63e33474cb05636404588ece5'}
        @param[in/out] results: 表拉取填充结果
            like:
            {'表名':[内容列表], '表名':[内容列表]}
        @return True:成功 False:失败
        '''
        if dbsource == 'mysql':
            data = requestScheduler(
                'mysql', 'do_search', dbname, table_name, search_condition)
        elif dbsource == 'mongo':
            data = requestScheduler(
                'mongo', 'do_search', dbname, table_name, search_condition)
        else:
            raise Exception('no db source could be matched!')
        self.preprocess_to_kv(data, table_name, results)

        return True

    def clean_invalid_data(self, ori_results) -> bool:
        '''
        @brief 清理无效数据
        @param[in/out] kv_result:待清理的字典，亦即输出字典
        '''
        check_list = {'is_valid': 1, 'deleted': 0,
                      'is_deleted': 0, 'is_del': 0}
        if (isinstance(ori_results, list)):
            for ori_result in ori_results[:]:
                if self.clean_invalid_data(ori_result):
                    ori_results.remove(ori_result)
        elif (isinstance(ori_results, dict)):
            for check_key in list(check_list.keys()):
                if check_key in list(ori_results.keys()):
                    if (isinstance(ori_results[check_key], bytes)):
                        check_value = ord(ori_results[check_key])
                        if(check_value != check_list[check_key]):
                            return True
                    elif (isinstance(ori_results[check_key], int) or
                          isinstance(ori_results[check_key], bool)):
                        check_value = int(ori_results[check_key])
                        if(check_value != check_list[check_key]):
                            return True
            for ori_key in list(ori_results.keys()):
                if (isinstance(ori_results[ori_key], dict)):
                    if self.clean_invalid_data(ori_results[ori_key]):
                        del ori_results[ori_key]
                elif (isinstance(ori_results[ori_key], list)):
                    self.clean_invalid_data(ori_results[ori_key])
        else:
            raise Exception(
                'An unhandled type appears when the \'clean_invalid_data\' function is called')

        return False

    def preprocess_to_kv(self, ori_results: list, table_name: str, kv_results: dict) -> None:
        '''
        @brief 数据预处理
        @param[in] ori_results: 纯原始表数据
        @param[in] table_name: 表名
        @param[in/out] kv_results: 处理后结果
        @return 无
        '''
        try:
            if len(ori_results) <= 0:
                return
            self.clean_invalid_data(ori_results)
            if table_name not in kv_results:
                kv_results[table_name] = []
            if not isinstance(ori_results, list):
                kv_results[str(table_name)].append(ori_results)
            else:
                kv_results[str(table_name)].extend(ori_results)
        except:
            logging.warn('preprocess_to_kv call failed![%s]' % (
                traceback.format_exc()))
        return


def getConfig(typeid: int, main_tables_config: dict) -> dict:
    '''
    @brief 获取指定typeid的配置信息
    @param[in] typeid: 指定id
    @param[in] main_tables_config: 表信息的主配置
    @return  返回指定typeid的配置信息
    '''
    doctype_conf_name = 'doctype'
    for tables in main_tables_config:
        if doctype_conf_name not in tables:
            return None
        if tables[doctype_conf_name] == typeid:
            # 调整配置结构为{'subtables':{'table_name':{'keys':{'key_name':{}}}}
            new_subtables = {}
            for subtable in tables['subtables']:
                table_name = subtable['name']
                new_keys = {}
                for key in subtable['keys']:
                    key_name = key['name']
                    new_keys[key_name] = copy.deepcopy(key)
                subtable_copy = copy.deepcopy(subtable)
                subtable_copy['keys'] = new_keys
                new_subtables[table_name] = subtable_copy
            return new_subtables
    return None


class DataBuilderMain:
    '''
    @brief 生成建库doc主接口类
    '''

    def __init__(self, doctype: int, docname: str, config: dict, env: str):
        self.doctype = doctype
        self.docname = docname
        self.loader = DataLoader()
        self.env = env  # config.get('env')
        config = getConfig(doctype, config)  # config.get('tables', {}))
        if config is None:
            raise Exception("get config fail![%d]" % (doctype))
        self.tables = config

    def __find_value_from_single_key(self, tables: list, find_condition: dict, filt_keys: list) -> list:
        '''
        @brief 根据条件查找表数据
        @param[in] tables: 数据库表结果列表
        @param[in] find_condition: 查找条件
        @param[in] filt_key: 筛留键名
        @return 匹配结果列表
            like: [{'filt_key1':v1, 'filt_key2':v2]
        '''
        filt_values = []
        for table in tables:
            filt_value = {}
            if (set(table.items()).issubset(find_condition.items())):
                # 查到该数据存在
                for filt_key in filt_keys:
                    if filt_key not in table:
                        return []
                    filt_value[filt_key] = table[filt_key]
                filt_values.append(filt_value)

        return filt_values

    def __consist_search_condition(self, father_table_relations: dict, pull_results: dict) -> []:
        '''
        @brief 根据父表关系，获取子表查询条件
        @param[in] father_table_relations: 父子表关系
        @param[in] pull_results: 刚拉取的表结果 | 不可更改
        @return 查询条件
            like: [{'condition':{'filt_key1':v1, 'filt_key2':v2}}
                   {'relation':{'父表名称1':父表idx}}
                  ]
        '''
        # 从单表获取query的kv
        # like: {'表名':[{'filt_key1':v1, 'filt_key2':v2}]}
        preprocess_result = {}
        for (table_name, kv_list) in father_table_relations.items():
            father_table_name = table_name
            if father_table_name not in pull_results:
                raise Exception('父表数据不存在！')

            for father_item in pull_results[father_table_name]:
                condition_item = {}
                for kv in kv_list:
                    fkey = kv['fkey']
                    if 'skey' in kv:
                        skey = kv['skey']
                        if fkey not in father_item:
                            raise Exception(
                                '父表数据中不存在key[%s]！check config?' % (fkey))
                        if skey in condition_item:
                            raise Exception('键重复[%s]!check config？' % (skey))
                        condition_item[skey] = father_item[fkey]
                if len(condition_item) <= 0:
                    continue
                if father_table_name not in preprocess_result:
                    preprocess_result[father_table_name] = []
                preprocess_result[father_table_name].append(condition_item)

        # 合并转换成最终形式
        # like: [{'condition':{'filt_key1':v1, 'filt_key2':v2}}
        #        {'relation':{'父表名称1':父表idx}}
        #        {'index':index}
        #       ]
        results = []
        last_results = []
        for (father_table_name, single_table_results) in preprocess_result.items():
            cur_results = []
            remove_idx = set()
            for (item_idx, father_items) in enumerate(single_table_results):
                if len(results) <= 0:
                    cur_result_item = {}
                    temp_father_items = copy.deepcopy(father_items)
                    cur_result_item['condition'] = temp_father_items
                    cur_result_item['relation'] = {father_table_name: item_idx}
                    cur_results.append(cur_result_item)
                else:
                    for (idx, result) in enumerate(last_results):
                        cur_result_item = result
                        remove_idx.add(idx)
                        temp_father_items = copy.deepcopy(father_items)
                        cur_result_item['condition'] = dict(
                            temp_father_items.items() | cur_result_item['condition'].items())
                        cur_result_item['relation'][father_table_name] = item_idx

            # 清除上一次results结果
            for idx in remove_idx:
                for (cur_idx, result) in enumerate(last_results[:]):
                    if cur_idx == idx:
                        last_results.remove(result)
            results.extend(last_results)

            # 重新赋值，开始新一轮迭代
            last_results = cur_results

        # 最后一次迭代赋值
        results.extend(last_results)
        return results

    def __check_is_sub_path(self, table_name: str) -> bool:
        '''
        @brief 判断表是否为子目录
        '''
        if len(table_name.split('.')) > 1:
            return True
        return False

    def __load_sub_path_data(self):
        return False

    def __check_data_pull_over(self, pull_results: dict):
        '''
        @brief 检查数据是否处理完毕
        @param[in] pull_results: 拉取的结果
        @return True: 处理完  False:未处理完
        '''
        is_over = True
        for (table_name, result_items) in pull_results:
            for result_item in result_items:
                if '__relation__' in result_item:
                    if len(list(result_item['__relation__'].keys())) > 1:
                        raise Exception('__relation__is not as expected!')
                    father_table_name = list(
                        result_item['__relation__'].keys())[0]
                    father_table_idx = list(
                        result_item['__relation__'].values())[0]
                    if len(pull_results[father_table_name]) > father_table_idx + 1:
                        is_over = False
                        return is_over
        return is_over

    def __pull_data(self, doctype: int, tables: dict, prikey: str, pull_results: dict):
        '''
        @brief 拉取数据
        @param[in] doctype: doc类型
        @param[in] tables: 数据库表配置列表
        @param[in] prikey: 待查询的主键key
        @param[out] pull_results: 数据拉取结果
            like: {'表名':[],'表名':[]}
        @return 0:成功  -1:失败
        '''
        for table in list(tables.values()):
            db_name = table['db']
            table_name = table['name']
            pull_results[table_name] = []
            if self.env != "pre" and self.env != "production":
                db_name = db_name + "_bigdata"

            # 路径表，先取数据
            flag = True
            if self.__check_is_sub_path(table_name):
                # 取得数据
                flag = False
                data = []
                relation = []
                for (fname, fdict) in table['father'].items():
                    for kv in fdict:
                        if 'skey' in kv:
                            flag = True
                            continue
                        if fname in pull_results and len(pull_results[fname]) > 0:
                            if len(table['father'][fname]) > 1:
                                raise Exception('Unknown Error!')
                            valid_father_table_name = fname
                            for (father_idx, father_item) in enumerate(pull_results[valid_father_table_name]):
                                fkey = kv['fkey']
                                if isinstance(father_item[fkey], list):
                                    data_item = father_item[fkey]
                                    data.extend(list(data_item))
                                    for data_item in data:
                                        relation.append(
                                            {valid_father_table_name: father_idx})
                                else:
                                    for (ik, iv) in father_item[fkey].items():
                                        item_dict = {}
                                        for k, v in table['keys'].items():
                                            if v['scope'] == '__KEYS__':
                                                item_dict[v['name']] = ik
                                            elif v['scope'] == '__VALUES__':
                                                item_dict[v['name']] = iv
                                            else:
                                                raise Exception(
                                                    'invalid scope param!')
                                        # 扔掉空数据
                                        if isinstance(item_dict[v['name']], dict) or isinstance(item_dict[v['name']], list):
                                            if not item_dict[v['name']]:
                                                continue
                                        data.append(item_dict)
                                        relation.append(
                                            {valid_father_table_name: father_idx})
                        elif str(fname) == str(table_name):
                            # 父表与自己相等 【trick】
                            pos = 0
                            while(pos < len(data)):
                                last_pos = pos
                                pos = len(data)
                                valid_father_table_name = fname
                                for (father_idx, father_item) in enumerate(data):
                                    if (father_idx < last_pos):
                                        continue
                                    fkey = kv['fkey']
                                    if isinstance(father_item[fkey], list):
                                        data_item = father_item[fkey]
                                        data.extend(list(data_item))
                                        for data_item in data:
                                            relation.append(
                                                {valid_father_table_name: father_idx})
                                    else:
                                        for (ik, iv) in father_item[fkey].items():
                                            item_dict = {}
                                            for k, v in table['keys'].items():
                                                if v['scope'] == '__KEYS__':
                                                    item_dict[v['name']] = ik
                                                elif v['scope'] == '__VALUES__':
                                                    item_dict[v['name']] = iv
                                                else:
                                                    raise Exception(
                                                        'invalid scope param!')
                                            # 扔掉空数据
                                            if isinstance(item_dict[v['name']], dict) or isinstance(item_dict[v['name']], list):
                                                if not item_dict[v['name']]:
                                                    continue
                                            data.append(item_dict)
                                            relation.append(
                                                {valid_father_table_name: father_idx})
                self.loader.clean_invalid_data(data)

            search_conditions = []
            search_condition_item = {}
            search_condition_item['condition'] = {}
            search_condition_item['relation'] = {}
            # 没有父表
            if 'father' not in table:
                dict_key = table['prikey']
                search_condition_item['condition'][dict_key] = prikey
                search_conditions.append(search_condition_item)
            elif flag:
                # 有父表
                search_conditions = self.__consist_search_condition(
                    table['father'], pull_results)
                if not search_conditions:
                    continue
            else:
                search_conditions.append(search_condition_item)

            has_inserted_value = set()
            for search_condition in search_conditions:
                begin_len = 0
                if table_name in pull_results:
                    begin_len = len(pull_results[table_name])
                if self.__check_is_sub_path(table_name):
                    if len(search_condition['condition']) <= 0:
                        # 父表纯路径
                        for data_item in data:
                            self.loader.preprocess_to_kv(
                                data_item, table_name, pull_results)
                        index_dict = {}
                        for i in range(len(pull_results[table_name]) - begin_len):
                            pull_results[table_name][i +
                                                     begin_len]['__relation__'] = relation[i]
                            father_index = list(relation[i].values())[0]
                            if father_index not in index_dict:
                                index_dict[father_index] = 0
                            else:
                                index_dict[father_index] = index_dict[father_index] + 1
                            pull_results[table_name][i +
                                                     begin_len]['__index__'] = index_dict[father_index]
                        break
                    else:
                        # 父表路径和条件表
                        success = True
                        for data_item in data[:]:
                            success = True
                            for (ikey, ivalue) in search_condition['condition'].items():
                                if ikey not in data_item:
                                    success = False
                                    break
                                if ivalue != data_item[ikey]:
                                    success = False
                                    break
                            if success:
                                has_inserted_value.add(
                                    list(search_condition['relation'].values())[0])
                                data_item_copy = copy.deepcopy(data_item)
                                data_item_copy['relation'] = search_condition['relation']
                                self.loader.preprocess_to_kv(
                                    data_item_copy, table_name, pull_results)
                                break
                else:
                    if (self.loader.do_search(db_name, table['source'], table_name, search_condition['condition'], pull_results) != True):
                        logging.warn('do_search [%s] failed!' % (table_name))
                        return -1
                index_dict = {}
                for i in range(len(pull_results[table_name]) - begin_len):
                    if len(search_condition['relation']) <= 0:
                        pull_results[table_name][(-i - 1)]['__index__'] = i
                    else:
                        pull_results[table_name][(-i - 1)
                                                 ]['__relation__'] = search_condition['relation']
                        father_index = i
                        if len(search_condition['relation']) > 0:
                            father_index = list(
                                search_condition['relation'].values())[0]
                            if father_index not in index_dict:
                                index_dict[father_index] = 0
                            else:
                                index_dict[father_index] = index_dict[father_index] + 1
                        pull_results[table_name][(-i - 1)]['__index__'] = len(
                            pull_results[table_name]) - begin_len - index_dict[father_index] - 1

        return 0

    def __clean_data(self, doctype, pull_results, clean_results):
        '''
        @brief 数据清洗
        @param[in]  doctype 文档类型
        @param[in]  pull_results 拉取数据结果
        @param[out] clean_results 清洗后结果
        '''
        # 开始清洗，去掉非建库项
        clean_results_item = {}
        for (table_name, value_list) in pull_results.items():
            if table_name not in self.tables:
                return -1

            useful_key = set(self.tables[table_name]['keys'].keys())
            useful_key.add('__relation__')
            useful_key.add('__index__')
            clean_result = []
            for value in value_list:
                clean_result_item = {}
                for (k, v) in value.items():
                    if k in useful_key:
                        clean_result_item[k] = v
                clean_result.append(clean_result_item)
            clean_results_item[table_name] = clean_result

        clean_results.append(clean_results_item)

        return 0

    def full_empty_json(self, prikey, pull_table_time):
        doc = {}
        doc["typeid"] = self.doctype
        doc["segnum"] = 0
        doc["segments"] = []
        doc["docid"] = prikey
        doc["timestamp"] = pull_table_time

        return json.dumps(doc, cls=DateEncoder, ensure_ascii=False)

    def run(self, prikey):
        '''
        @brief 执行函数
        @param[in] prikey 主键值
        '''
        # 查询表
        pull_results = {}
        pull_table_time = int(time.time() * 1000)  # ms
        ret = self.__pull_data(self.doctype, self.tables, prikey, pull_results)
        if ret < 0:
            return self.full_empty_json(prikey, pull_table_time)
        #logging.debug(json.dumps(pull_results, cls=DateEncoder, ensure_ascii=False))

        # 数据清洗
        clean_results = []
        ret = self.__clean_data(self.doctype, pull_results, clean_results)
        if ret < 0:
            return self.full_empty_json(prikey, pull_table_time)
        #logging.debug(json.dumps(clean_results, cls=DateEncoder, ensure_ascii=False))

        # 填充建库数据
        builder = DataBuilder(self.doctype, self.docname, self.tables)
        build_results = []
        builder.do_build(pull_table_time, prikey, clean_results, build_results)

        if (len(build_results) <= 0):
            return self.full_empty_json(prikey, pull_table_time)
        else:
            ret_json = json.dumps(
                build_results[0], cls=DateEncoder, ensure_ascii=False)
            return ret_json

        return self.full_empty_json(prikey, pull_table_time)
