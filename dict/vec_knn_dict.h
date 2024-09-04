#ifndef DEMO_RECOMMEND_SRC_DICT_VEC_KNN_DICT_H
#define DEMO_RECOMMEND_SRC_DICT_VEC_KNN_DICT_H

#include <map>
#include <string>
#include <vector>

namespace demo {
namespace recommend {

class VecKnnDict {
public:
    struct KnnItem {
        uint32_t item;
        float knn_score;
    };

    typedef std::map<std::string, std::vector<KnnItem> > vec_knn_dict_t;
    typedef std::map<std::string, std::vector<KnnItem> >::iterator vec_knn_dict_it_t;
    typedef std::map<std::string, std::vector<KnnItem> >::const_iterator vec_knn_dict_const_it_t;

    typedef std::map<uint32_t, std::string> shortid2md5id_t;
    typedef std::map<uint32_t, std::string>::iterator shortid2md5id_it_t;
    typedef std::map<uint32_t, std::string>::const_iterator shortid2md5id_const_it_t;

    // 热加载数据
    int do_reload(const std::string & path, const std::string & conf_file);

    void un_load()
    {
        _dict.clear();
        _shortid2md5id.clear();
    }

    // 判断是否需要、以及可以重新加载数据了
    int check_can_reload(const std::string & path, const std::string & conf_file);

    bool has(const std::string md5id)
    {
        return _dict.find(md5id) != _dict.end();
    }
    void get(const std::string md5id, std::vector<std::pair<std::string, float> >& recall_result);

    int after_load_check() {return 0;}

private:
    vec_knn_dict_t _dict;
    shortid2md5id_t _shortid2md5id;
};

}
}
#endif  //DEMO_RECOMMEND_SRC_DICT_VEC_KNN_DICT_H

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
