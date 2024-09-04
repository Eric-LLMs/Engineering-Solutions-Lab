#ifndef  DEMO_RECOMMEND_SRC_DICT_SONG_NAME_TIME_H
#define  DEMO_RECOMMEND_SRC_DICT_SONG_NAME_TIME_H

#include <map>
#include <string>

namespace demo {
namespace recommend {

class SongNameTimeDict {
public:
    struct SongNameInfo {
        long year_hottest;
        long year_earliest;
    };

    typedef std::map<std::string, SongNameInfo> song_name_time_dict_t;
    typedef std::map<std::string, SongNameInfo>::iterator song_name_time_dict_it_t;
    typedef std::map<std::string, SongNameInfo>::const_iterator song_name_time_dict_const_it_t;

    // 热加载数据
    int do_reload(const std::string & path, const std::string & conf_file);

    void un_load()
    {
        _dict.clear();
    }

    // 判断是否需要、以及可以重新加载数据了
    int check_can_reload(const std::string & path, const std::string & conf_file);

    // 获得词典
    const song_name_time_dict_t& get_dict()
    {
        return _dict;
    }

    const SongNameInfo* get(const std::string& key)
    {
        song_name_time_dict_const_it_t it = _dict.find(key);
        if (it == _dict.end()) {
            return NULL;
        }
        return &it->second;
    }

    int after_load_check() {return 0;}
private:
    song_name_time_dict_t _dict;
};

}
}
#endif  //DEMO_RECOMMEND_SRC_DICT_SONG_NAME_TIME_H

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
