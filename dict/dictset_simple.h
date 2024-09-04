#ifndef  DEMO_RECOMMEND_MAP_BY_DICTSET_H
#define  DEMO_RECOMMEND_MAP_BY_DICTSET_H

#include "util.h"
#include <logger.h>
#include "dictset.h"

namespace DEMO {
namespace recommend {

#define GET_VALUE_I_COL(found_item, idx, val) \
do { \
    if (SEEK_SUCC != _dict_set->get_value_i_col(found_item, idx, val)) { \
        EDU_LOG(SEARCH_WARN, "get %d-th value failed", idx); \
        return -1; \
    } \
} while (0)

#define SEARCH_DICT_SET() \
    if (_dict_set == NULL) { \
        EDU_LOG(SEARCH_WARN, "_dict_set is NULL"); \
        return -1; \
    } \
    item_t* found_item = NULL; \
    if (dset_search_item_key(_dict_set, (void*)key.c_str(), &found_item, NULL) != 1) { \
        return 1; \
    }


class DictsetSimple {

    DictSet* _dict_set;
public:
    DictsetSimple(): _dict_set(NULL) {}
    virtual ~DictsetSimple() 
    {
        if (_dict_set != NULL) {
            unload();
        }
    }

    int load(const std::string& path, const std::string& name) 
    {
        _dict_set = dset_create();
        if (!_dict_set) {
            EDU_LOG(SEARCH_FATAL, "can't create dict");
        }
        if (dset_binary_load(_dict_set, path.c_str(), name.c_str()) != 0){ 
            if (_dict_set) {
                dset_binary_release(_dict_set);
                _dict_set = NULL;
            }
            std::string file_name = path + "/" + name;
            EDU_LOG(SEARCH_WARN, "can't load dict:[%s]", file_name.c_str());
            return -1; 
        }   
        return 0;
    }

    template <typename TValue>
    int find(const std::string& key, TValue& val) 
    {
        SEARCH_DICT_SET();
        GET_VALUE_I_COL(found_item, 0, val);
        return 0;
    }

    template <typename TValue, typename TValue1>
    int find2(const std::string& key, TValue& val, TValue1& val1) {
        SEARCH_DICT_SET();
        GET_VALUE_I_COL(found_item, 0, val);
        GET_VALUE_I_COL(found_item, 1, val1);
        return 0;
    }

    template <typename TValue, typename TValue1, typename TValue2>
    int find3(const std::string& key, TValue& val, TValue1& val1, TValue2& val2) 
    {
        SEARCH_DICT_SET();
        GET_VALUE_I_COL(found_item, 0, val);
        GET_VALUE_I_COL(found_item, 1, val1);
        GET_VALUE_I_COL(found_item, 2, val2);
        return 0;
    }

    template <typename TValue, typename TValue1, typename TValue2, typename TValue3>
    int find4(const std::string& key, TValue& val, TValue1& val1, TValue2& val2, TValue3& val3) 
    {
        SEARCH_DICT_SET();
        GET_VALUE_I_COL(found_item, 0, val);
        GET_VALUE_I_COL(found_item, 1, val1);
        GET_VALUE_I_COL(found_item, 2, val2);
        GET_VALUE_I_COL(found_item, 3, val3);
        return 0;
    }

    template <typename TValue, typename TValue1, typename TValue2, typename TValue3, typename TValue4>
    int find5(const std::string& key, TValue& val, TValue1& val1, TValue2& val2, TValue3& val3, TValue4& val4) 
    {
        SEARCH_DICT_SET();
        GET_VALUE_I_COL(found_item, 0, val);
        GET_VALUE_I_COL(found_item, 1, val1);
        GET_VALUE_I_COL(found_item, 2, val2);
        GET_VALUE_I_COL(found_item, 3, val3);
        GET_VALUE_I_COL(found_item, 4, val4);
        return 0;
    }

    template <typename TValue>
    int find_array_value(const std::string& key, std::vector<TValue>& val_arr, int cnt)
    {
        val_arr.clear();
        if (cnt <= 0) {
            return 0;
        }
        val_arr.resize(cnt);
        SEARCH_DICT_SET();
        for (int i = 0; i < cnt; ++i) {
            GET_VALUE_I_COL(found_item, i, val_arr[i]);
        }
        return 0;
    }

    void unload() {
        if (_dict_set) {
            dset_binary_release(_dict_set);
            _dict_set = NULL;
        }
    }
};

}
}

#endif  //DEMO_RECOMMEND_MAP_BY_DICTSET_H

