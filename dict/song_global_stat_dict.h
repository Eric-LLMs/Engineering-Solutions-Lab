#ifndef  DEMO_RECOMMEND_SRC_DICT_SONG_GLOBAL_STAT_DICT_H
#define  DEMO_RECOMMEND_SRC_DICT_SONG_GLOBAL_STAT_DICT_H

#include <map>
#include <string>

namespace demo {
namespace recommend {

class GlobalPlayStatDict {
public:
    struct PlayStat {
        int play_cnt;
        int play_finish_cnt;
        int q_call_cnt; // query主动召唤个数
        float finish_rate;
    };

    typedef std::map<std::string, PlayStat> play_stat_dict_t;
    typedef std::map<std::string, PlayStat>::iterator play_stat_dict_it_t;
    typedef std::map<std::string, PlayStat>::const_iterator play_stat_dict_const_it_t;

    // 热加载数据
    int do_reload(const std::string & path, const std::string & conf_file);

    void un_load()
    {
        _dict.clear();
    }

    // 判断是否需要、以及可以重新加载数据了
    int check_can_reload(const std::string & path, const std::string & conf_file);

    // 获得词典
    const play_stat_dict_t& get_dict()
    {
        return _dict;
    }
    int get_q_call_cnt(const std::string& key) {
        play_stat_dict_const_it_t it = _dict.find(key);
        if (it == _dict.end()) {
            return 0;
        }
        return it->second.q_call_cnt;
    }

    int after_load_check() {return 0;}

private:
    play_stat_dict_t _dict;
};

}
}
#endif  //DEMO_RECOMMEND_SRC_DICT_SONG_GLOBAL_STAT_DICT_H

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
