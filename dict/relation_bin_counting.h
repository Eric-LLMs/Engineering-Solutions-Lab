#ifndef DEMO_RECOMMEND_SRC_DICT_RELATION_BIN_COUNTING_H
#define DEMO_RECOMMEND_SRC_DICT_RELATION_BIN_COUNTING_H

#include <map>
#include <string>
#include "dict/dictset_simple.h"

namespace demo {
namespace recommend {

class RelationBinCountingDict {
public:
    
    int do_reload(const std::string& path, const std::string& conf_file) {
        std::string file_name = path + "/" + conf_file;
        un_load();
        return _dict.load("./", file_name);
    }

    void un_load() {
        _dict.unload();
    }

    // 判断是否需要、以及可以重新加载数据了
    int check_can_reload(const std::string & path, const std::string & conf_file) {
        return 1;
    }

    // 获得词典
    const DictsetSimple& get_dict()
    {
        return _dict;
    }
    DictsetSimple* get_dict_pointer() {
        return &_dict;
    }
    int after_load_check() {return 0;}

private:
    DictsetSimple _dict;
};

} // end namespace recommend
} // end namespace DEMO
#endif // DEMO_RECOMMEND_SRC_DICT_ENTITY_BIN_COUNTING_H 
