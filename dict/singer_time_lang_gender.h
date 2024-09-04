#ifndef  DEMO_RECOMMEND_SRC_DICT_SINGER_TIME_LANG_GENDER_H
#define  DEMO_RECOMMEND_SRC_DICT_SINGER_TIME_LANG_GENDER_H

#include <map>
#include <string>

namespace demo {
namespace recommend {

class SingerDetailDict {
public:
    struct SingerInfo {
        int singer_year;
        int lang;
        int gender;
        int lang_gender;
    };
    int max_lang;
    int max_gender;
    int max_lang_gender;

    typedef std::map<std::string, SingerInfo> singer_detail_dict_t;
    typedef std::map<std::string, SingerInfo>::iterator singer_detail_dict_it_t;
    typedef std::map<std::string, SingerInfo>::const_iterator singer_detail_dict_const_it_t;

    // 热加载数据
    int do_reload(const std::string & path, const std::string & conf_file);

    void un_load()
    {
        _dict.clear();
    }

    // 判断是否需要、以及可以重新加载数据了
    int check_can_reload(const std::string & path, const std::string & conf_file);

    // 获得词典
    const singer_detail_dict_t& get_dict()
    {
        return _dict;
    }

    const SingerInfo* get(const std::string& key)
    {
        singer_detail_dict_const_it_t it = _dict.find(key);
        if (it == _dict.end()) {
            return NULL;
        }
        return &it->second;
    }

    int after_load_check() {return 0;}
private:
    singer_detail_dict_t _dict;
};

}
}
#endif  //DEMO_RECOMMEND_SRC_DICT_SINGER_TIME_LANG_GENDER_H

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
