#ifndef  DEMO_RECOMMEND_SRC_DICT_ENTITY_VEC_H
#define  DEMO_RECOMMEND_SRC_DICT_ENTITY_VEC_H

#include <logger.h>
#include <unordered_map>
#include <string>
#include <vector>

namespace demo {
namespace recommend {

class EntityVec {
public:
    EntityVec() :_buf(NULL) {}
    ~EntityVec() {
        if (_buf) {
            delete [] _buf;
        }
    }

    // 热加载数据
    int do_reload(const std::string & path, const std::string & conf_file);

    // 判断是否需要、以及可以重新加载数据了
    int check_can_reload(const std::string & path, const std::string & conf_file);

    void un_load()
    {
        _dict.clear();
        if (_buf != NULL) {
            delete [] _buf;
            _buf = NULL;
        }
    }

    bool has(const std::string& ent_name)
    {
        return _dict.find(ent_name) != _dict.end();
    }

    const float* get(const std::string& ent_name) {
        std::unordered_map<std::string, float*>::const_iterator it = _dict.find(ent_name);
        if (it == _dict.end()) {
            return NULL;
        }
        return it->second;
    }

    float cosine(const std::string& ent_name1, const std::string& ent_name2) {
        std::unordered_map<std::string, float*>::const_iterator it1 = _dict.find(ent_name1);
        std::unordered_map<std::string, float*>::const_iterator it2 = _dict.find(ent_name2);
        if (it1 == _dict.end() || it2 == _dict.end()) {
            return 0.;
        }
        float * vec1 = it1->second;
        float * vec2 = it2->second;
        float sc = 0.;
        for (int i = 1; i < _dim + 1; ++i) {
            sc += vec1[i] * vec2[i];
        }
        if (vec1[0] == 0. || vec2[0] == 0.) {
            return 0.;
        }
        sc = sc / vec1[0] / vec2[0];
        return sc;
    }

    float cosine(const std::string& ent_name, const float * vec, float vec_len) {
        std::unordered_map<std::string, float*>::const_iterator it1 = _dict.find(ent_name);
        if (it1 == _dict.end()) {
            return 0.;
        }
        const float * vec1 = it1->second;
        const float * vec2 = vec - 1;
        float sc = 0.;
        for (int i = 1; i < _dim + 1; ++i) {
            sc += vec1[i] * vec2[i];
        }
        if (vec1[0] == 0. || vec_len == 0.) {
            return 0.;
        }
        sc = sc / vec1[0] / vec_len;
        return sc;
    }

    int after_load_check() 
    {
        std::unordered_map<std::string, float*>::iterator it = _dict.begin();
        std::string item1 = it->first;
        float sc = cosine(item1, item1);
        if (sc < 0.99 || sc > 1.01) {
            EDU_LOG(SEARCH_WARN, "check failed, as cos('%s', '%s') = %f, not in range 0.99~1.01", 
                        item1.c_str(), item1.c_str(), sc);
            return -1;
        }
        if (_dict.size() > 1) {
            it++;
            std::string item2 = it->first;
            float sc = cosine(item1, item2);
            if (sc < - 1.01 || sc > 1.01) {
                EDU_LOG(SEARCH_WARN, "check failed, as cos('%s', '%s') = %f, not in range -1.01~1.01",
                        item1.c_str(), item2.c_str(), sc);
                return -1;
            }
        }
        return 0;
    }

private:
    float * _buf;
    int _dim;
    std::unordered_map<std::string, float*> _dict;
};

}
}
#endif  //DEMO_RECOMMEND_SRC_DICT_ENTITY_VEC_H

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
