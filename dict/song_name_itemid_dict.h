#ifndef  DEMO_RECOMMEND_SONG_NAME_ITEMID_DICT_H
#define  DEMO_RECOMMEND_SONG_NAME_ITEMID_DICT_H

#include <map>
#include <set>
#include <string>
#include <vector>
#include <ctime>
#include <algorithm>
#include "util.h"
#include <vector>
#include "../dict_set_mgr.h"
#include "dictset.h"
#include <logger.h>
#include "StringUtility.h"
#include <boost/algorithm/string.hpp>
#include <boost/lexical_cast.hpp>
#include <iostream>
#include "timer.h"
#include "fm_rank_common.h"

namespace demo {
namespace recommend {

typedef DictSetMgr<std::string, std::vector< std::pair<std::string, float>> > SongNameItemIdDictMgr;

class SongNameItemIdDict : public SongNameItemIdDictMgr {
public:
    int init(const std::string& path, const std::string& name) {
        return SongNameItemIdDictMgr::init(path.c_str(), name.c_str());
    }

    /**
     * 利用key从dict中获取vector
     * return true:success  false:failed
     */
    bool get_key_value(const std::string& key_id, 
            std::vector< std::pair<std::string, float> >& value_vector) {
        // 词典格式为：0->song_name, 1[]->md5id:score, md5id:score
        value_vector.clear();
        DictSet* dict_set = get();
        if (!dict_set) {
            EDU_LOG(SEARCH_WARN, "dict is not loaded");
            return false;
        }

        const unsigned int KEY_BUF_LEN = 500;
        char key_buf[KEY_BUF_LEN] = {'\0'};
        char *value_buf = NULL;
        item_t* found_item = NULL;
        if (snprintf(key_buf, KEY_BUF_LEN, key_id.c_str()) < 0) {
            EDU_LOG(SEARCH_WARN, "snprintf key_buf:[%s] error", key_id.c_str());
            return false;
        }
        if (dset_search_item_key(dict_set, key_buf, &found_item, NULL) != 1) {
            EDU_LOG(SEARCH_DEBUG, "search dictset not found key:[%s]", key_buf);
            return false;
        }
        EDU_LOG(SEARCH_DEBUG, "search dictset found key:[%s]", key_buf);

        if (dict_set->get_value_i_col(found_item, 0, value_buf) != SEEK_SUCC){
            EDU_LOG(SEARCH_WARN, "search dictset get value failed. key:[%s]", key_buf);
            return false;
        }
        std::string value_str = value_buf;
        std::vector<std::string> song_values;
        boost::split(song_values, value_str, boost::is_any_of(","));
        // 计算实际返回的相似歌曲数目
        int song_size = song_values.size();
        EDU_LOG(SEARCH_DEBUG, "dict-set key:[%s]", key_buf);
        std::vector<string> split_vec;
        for (int i = 0; i < song_size; ++i) {
            split_vec.clear();
            boost::split(split_vec, song_values[i], boost::is_any_of(":"));
            // md5:score
            if (split_vec.size() != 2) {
                EDU_LOG(SEARCH_WARN, "value:[%s] is not md5:score", 
                        song_values[i].c_str());
                continue;
            }
            try {
                float score_value = boost::lexical_cast<float>(split_vec[1]);
                value_vector.push_back(std::make_pair(split_vec[0], score_value));
                EDU_LOG(SEARCH_DEBUG, "value:[%s], weight:[%s]", 
                        split_vec[0].c_str(), split_vec[1].c_str());
            } catch (boost::bad_lexical_cast& e) {
                EDU_LOG(SEARCH_WARN, "get value_vector score_value:[%s] exception:[%s]", 
                        split_vec[1].c_str(), e.what());
                return false;
            }
        }
        std::sort(value_vector.begin(), value_vector.end(), 
                [](const std::pair<std::string, float> &a, const std::pair<std::string, float> &b) 
                { return a.second > b.second;} );
        return true;
    }
};

class SongNameAnnDict : public SongNameItemIdDict {};
class SongNameHotVersionDict : public SongNameItemIdDict {};
class SongListDict : public SongNameItemIdDict {};
}
}
#endif  //DEMO_RECOMMEND_SONG_NAME_ITEMID_DICT_H

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
