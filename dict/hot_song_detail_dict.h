#ifndef  DEMO_RECOMMEND_HOT_SONG_DETAIL_DICT_H
#define  DEMO_RECOMMEND_HOT_SONG_DETAIL_DICT_H

#include <map>
#include <set>
#include <string>
#include <vector>
#include <ctime>
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
#include "recommend_util.h"

namespace demo {
namespace recommend {


struct SongInfo {
    std::set<std::string> from_site_set;
    std::set<std::string> tag_set;
    std::vector<std::string> singer_vec;
    std::string language;
    std::string song_name;
    int hot;
    long publish_time;
    bool is_publish_time_valid;
};

typedef DictSetMgr<std::string, SongDetail> HotSongDetailDictMgr;

class HotSongDetailDict : public HotSongDetailDictMgr {
public:
    int init(const std::string& path, const std::string& name) {
        return HotSongDetailDictMgr::init(path.c_str(), name.c_str());
    }

    /**
     * 利用key从dict中获取vector
     * return true:success  false:failed
     */
    bool get_key_value(const std::string& key_id, 
            SongDetail& value) {
        // 词典格式为：0->song_id, 1->singer[], 2->song_name, 3->tag[], 4->publish, 5->hot, 6->from_site[] + source_site[], 7->lang, 8->best_version_id, 9->version
        DictSet* dict_set = get();
        if (!dict_set) {
            EDU_LOG(SEARCH_WARN, "dict is not loaded");
            return false;
        }
        // md5长度为128bits，每4bits一个char表示，共32个char
        const unsigned int KEY_BUF_LEN = 50;
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
        // 从found_item中获取具体信息
        std::vector<std::string> str_vec;
        std::string str_value;
        char* char_value = NULL;
        int int_value = 0;
        double double_value = 0.0;

        // singer_name
        if (dict_set->get_value_i_col(found_item, 0, char_value) != SEEK_SUCC){
            EDU_LOG(SEARCH_WARN, "search dictset get value failed. key:[%s]", key_buf);
            return false;
        }
        if (!char_value || _EMPTY_STR_FLAG == char_value) {
            str_value = "";
        } else {
            str_value = char_value;
        }
        str_vec.clear();
        boost::split(str_vec, str_value, boost::is_any_of("^"));
        value.singer_vec = str_vec;
        EDU_LOG(SEARCH_DEBUG, "dictset singer_name:[%s]", str_value.c_str());

        // song_name
        if (dict_set->get_value_i_col(found_item, 1, char_value) != SEEK_SUCC){
            EDU_LOG(SEARCH_WARN, "search dictset get value failed. key:[%s]", key_buf);
            return false;
        }
        if (!char_value || _EMPTY_STR_FLAG == char_value) {
            str_value = "";
        } else {
            str_value = char_value;
        }
        value.song_name = str_value;
        EDU_LOG(SEARCH_DEBUG, "dictset song_name:[%s]", str_value.c_str());

        // tag
        if (dict_set->get_value_i_col(found_item, 2, char_value) != SEEK_SUCC){
            EDU_LOG(SEARCH_WARN, "search dictset get value failed. key:[%s]", key_buf);
            return false;
        }
        if (!char_value || _EMPTY_STR_FLAG == char_value) {
            str_value = "";
        } else {
            str_value = char_value;
        }
        str_vec.clear();
        boost::split(str_vec, str_value, boost::is_any_of("^"));
        value.tag_set.clear();
        for (int i = 0; i < str_vec.size(); ++i) {
            value.tag_set.insert(str_vec[i]);
        }
        EDU_LOG(SEARCH_DEBUG, "dictset tag:[%s]", str_value.c_str());

        // publish
        if (dict_set->get_value_i_col(found_item, 3, char_value) != SEEK_SUCC){
            EDU_LOG(SEARCH_WARN, "search dictset get value failed. key:[%s]", key_buf);
            return false;
        }
        if (!char_value || _EMPTY_STR_FLAG == char_value) {
            str_value = "";
        } else {
            str_value = char_value;
        }
        int year, hour, week;
        time_t unix_time;
        get_time_from_date(str_value, year, hour, week, unix_time);
        value.publish_time = unix_time;
        value.is_publish_time_valid = (unix_time == 0) ? false : true;
        EDU_LOG(SEARCH_DEBUG, "dictset publish:[%s]", str_value.c_str());

        // hot
        if (dict_set->get_value_i_col(found_item, 4, int_value) != SEEK_SUCC){
            EDU_LOG(SEARCH_WARN, "search dictset get value failed. key:[%s]", key_buf);
            return false;
        }
        value.hot = int_value;
        EDU_LOG(SEARCH_DEBUG, "dictset hot:[%d]", int_value);

        // from_site
        if (dict_set->get_value_i_col(found_item, 5, char_value) != SEEK_SUCC){
            EDU_LOG(SEARCH_WARN, "search dictset get value failed. key:[%s]", key_buf);
            return false;
        }
        if (!char_value || _EMPTY_STR_FLAG == char_value) {
            str_value = "";
        } else {
            str_value = char_value;
        }
        str_vec.clear();
        boost::split(str_vec, str_value, boost::is_any_of("^"));
        value.from_site_set.clear();
        for (int i = 0; i < str_vec.size(); ++i) {
            value.from_site_set.insert(str_vec[i]);
        }
        EDU_LOG(SEARCH_DEBUG, "dictset from_site:[%s]", str_value.c_str());
        //source_site
        value.source_site_set.clear();
        for (int i = 0; i < str_vec.size(); ++i) {
            value.source_site_set.insert(str_vec[i]);
        }
        EDU_LOG(SEARCH_DEBUG, "dictset source_site:[%s]", str_value.c_str());

        // lang
        if (dict_set->get_value_i_col(found_item, 6, char_value) != SEEK_SUCC){
            EDU_LOG(SEARCH_WARN, "search dictset get value failed. key:[%s]", key_buf);
            return false;
        }
        if (!char_value || _EMPTY_STR_FLAG == char_value) {
            str_value = "";
        } else {
            str_value = char_value;
        }
        value.language = str_value;
        EDU_LOG(SEARCH_DEBUG, "dictset language:[%s]", str_value.c_str());

        // best_version_id
        if (dict_set->get_value_i_col(found_item, 7, char_value) != SEEK_SUCC){
            EDU_LOG(SEARCH_WARN, "search dictset get value failed. key:[%s]", key_buf);
            return false;
        }
        if (!char_value || _EMPTY_STR_FLAG == char_value) {
            str_value = "";
        } else {
            str_value = char_value;
        }
        value.best_version_id = str_value;
        EDU_LOG(SEARCH_DEBUG, "dictset best_version:[%s]", str_value.c_str());

        // version
        if (dict_set->get_value_i_col(found_item, 8, char_value) != SEEK_SUCC){
            EDU_LOG(SEARCH_WARN, "search dictset get value failed. key:[%s]", key_buf);
            return false;
        }
        if (!char_value || _EMPTY_STR_FLAG == char_value) {
            str_value = "";
        } else {
            str_value = char_value;
        }
        value.version = str_value;
        EDU_LOG(SEARCH_DEBUG, "dictset version:[%s]", str_value.c_str());

        return true;
    }

protected:
    const std::string _EMPTY_STR_FLAG = "_NULL_";
};

// HotSongDetailDict* hot_song_detail_dict(NULL);
}
}
#endif  //DEMO_RECOMMEND_HOT_SONG_DETAIL_DICT_H

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
