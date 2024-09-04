#ifndef  DUER_RECOMMEND_SRC_DICT_SINGER_RECALL_DICT_H
#define  DUER_RECOMMEND_SRC_DICT_SINGER_RECALL_DICT_H

#include <map>
#include <string>
#include <vector>

namespace demo {
namespace recommend {

class SingerRecallDict {
public:
    struct RecallItem {
        std::string item;
        int hot;
    };

    typedef std::map<std::string, std::vector<RecallItem> > singer_recall_dict_t;
    typedef std::map<std::string, std::vector<RecallItem> >::iterator singer_recall_dict_it_t;
    typedef std::map<std::string, std::vector<RecallItem> >::const_iterator singer_recall_dict_const_it_t;

    // 热加载数据
    int do_reload(const std::string & path, const std::string & conf_file);

    void un_load()
    {
        _dict.clear();
    }

    // 判断是否需要、以及可以重新加载数据了
    int check_can_reload(const std::string & path, const std::string & conf_file);

    // 获得词典
    const singer_recall_dict_t& get_dict()
    {
        return _dict;
    }

    int after_load_check() {return 0;}
private:
    singer_recall_dict_t _dict;
};

}
}
#endif  //DEMO_RECOMMEND_SRC_DICT_SINGER_RECALL_DICT_H

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
