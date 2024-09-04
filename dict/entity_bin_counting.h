#ifndef DEMO_RECOMMEND_SRC_DICT_ENTITY_BIN_COUNTING_H
#define DEMO_RECOMMEND_SRC_DICT_ENTITY_BIN_COUNTING_H

#include <map>
#include <string>

namespace DEMO {
namespace recommend {

class EntityBinCountingDict {
public:
    struct bin_counting_t {
        float finish_cnt;
        float unfinish_cnt;
        float finish_ratio;
        bin_counting_t(float finish_cnt, float unfinish_cnt, float finish_ratio): finish_cnt(finish_cnt), unfinish_cnt(unfinish_cnt), finish_ratio(finish_ratio) {}
    };
    
    typedef std::map<std::string, bin_counting_t> entity_bin_counting_dict_t;
    typedef std::map<std::string, bin_counting_t>::iterator entity_bin_counting_dict_it_t;
    typedef std::map<std::string, bin_counting_t>::const_iterator entity_bin_counting_dict_const_it_t;
    
    int do_reload(const std::string& path, const std::string& conf_file);

    void un_load() {
        _dict.clear();
    }

    // 判断是否需要、以及可以重新加载数据了
    int check_can_reload(const std::string & path, const std::string & conf_file);

    // 获得词典
    const entity_bin_counting_dict_t& get_dict()
    {
        return _dict;
    }
    bool get_finish_cnt(const std::string& key, float* value) {
        auto it = _dict.find(key);
        if (it == _dict.end()) {
            return false;
        }
        *value = it->second.finish_cnt;
        return true;
    }
    bool get_unfinish_cnt(const std::string& key, float* value) {
        auto it = _dict.find(key);
        if (it == _dict.end()) {
            return false;
        }
        *value = it->second.unfinish_cnt;
        return true;
    }
    bool get_finish_ratio(const std::string& key, float* value) {
        auto it = _dict.find(key);
        if (it == _dict.end()) {
            return false;
        }
        *value = it->second.finish_ratio;
        return true;
    }
    bool get_feature(const std::string& key, float* finish_cnt, float* unfinish_cnt, float* finish_ratio) {
        auto it = _dict.find(key);
        if (it == _dict.end()) {
            return false;
        }
        *finish_cnt = it->second.finish_cnt;
        *unfinish_cnt = it->second.unfinish_cnt;
        *finish_ratio = it->second.finish_ratio;
        return true;
    }
    int after_load_check() {return 0;}

private:
    entity_bin_counting_dict_t _dict;
};

} // end namespace recommend
} // end namespace DEMO
#endif // DEMO_RECOMMEND_SRC_DICT_ENTITY_BIN_COUNTING_H 
