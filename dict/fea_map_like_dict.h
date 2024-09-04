#ifndef  DEMO_RECOMMEND_SRC_DICT_FEA_MAP_LIKE_DICT_H
#define  DEMO_RECOMMEND_SRC_DICT_FEA_MAP_LIKE_DICT_H

#include <logger.h>
#include "fea_map_dict.h"

namespace demo {
namespace recommend {

class FeaMapLikeDict {
public:

    // 热加载数据
    int do_reload(const std::string & path, const std::string & conf_file)
    {
        return _fea_map.load(path, conf_file);
    }

    // 判断是否需要、以及可以重新加载数据了
    int check_can_reload(const std::string & path, const std::string & conf_file)
    {
        return 1;
    }

    void un_load()
    {
        _fea_map.unload();
    }

    int get(const std::string& key, std::vector<int>& fea_ids, std::vector<float>& fea_vals) const
    {
        return _fea_map.get(key, fea_ids, fea_vals);
    }

    int after_load_check()
    {
        /*
        std::string id = "4d3a962b181fc4b6e5486adddbf9c5b4";
        std::vector<int> fea_ids;
        std::vector<float> fea_vals;
        int ret = _fea_map.get(id, fea_ids, fea_vals);
        printf("%d\n", ret);
        if (fea_ids.size() > 0) {
            printf("%d\n", fea_ids[0]);
        }
        return ret;
        */
        return 0;
    }

private:
    FeaMapDict _fea_map;
};

}
}
#endif  //DEMO_RECOMMEND_SRC_DICT_FEA_MAP_LIKE_DICT_H

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
