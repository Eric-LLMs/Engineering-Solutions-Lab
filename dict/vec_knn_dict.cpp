#include "vec_knn_dict.h"

#include <logger.h>
#include <fstream>
#include <boost/algorithm/string.hpp>
#include <boost/lexical_cast.hpp>

namespace demo {
namespace recommend {

// check if can reload now
int VecKnnDict::check_can_reload(const std::string & path, const std::string & conf_file)
{
    std::string file = path + "/" + conf_file;
    std::ifstream fin(file.c_str());
    if (!fin) {
        EDU_LOG(SEARCH_WARN, "open file %s failed", file.c_str());
        return -1;
    }
    std::string read_line;
    std::getline(fin, read_line);
    fin.close();
    if (read_line.size() && read_line.c_str()[0] == '#') {
        int update_token = -1;
        sscanf(read_line.c_str(), "#%d", &update_token);
        if (update_token > 0) {
            return update_token;
        }
    }
    return 1;
}

static int md5id2uint32(const std::string& str, uint32_t& val)
{
    if (str.size() < 8) {
        return -1;
    }
    const char * s = str.c_str();
    val = 0;
    for (int i = 0; i < 8; ++i) {
        val = val << 4;
        if (s[i] >= '0' && s[i] <= '9') {
            val |= (s[i] - '0');
        } else if (s[i] >= 'a' && s[i] <= 'f') {
            val |= (s[i] - 'a' + 10);
        } else if (s[i] >= 'A' && s[i] <= 'F') {
            val |= (s[i] - 'A' + 10);
        } else {
            return -1;
        }
    }
    return 0;
}

// 热加载数据
int VecKnnDict::do_reload(const std::string & path, const std::string & conf_file)
{
    _dict.clear();
    _shortid2md5id.clear();

    std::string file = path + "/" + conf_file;
    std::ifstream fin(file.c_str());
    if (!fin) {
        EDU_LOG(SEARCH_WARN, "open file %s failed", file.c_str());
        return -1; 
    }
    std::string read_line;
    int error = 0;
    int line_no = 0;
    while (std::getline(fin, read_line)) {
        if (error > 5) {
            fin.close();
            EDU_LOG(SEARCH_WARN, "too many(>5) error found!");
            return -1;
        }
        if (read_line.empty()) {
            continue;
        }

        if (read_line.c_str()[0] == '#') {
            continue;
        }
        line_no++;

        std::vector<std::string> str_vector;
        boost::split(str_vector, read_line, boost::is_any_of("\t"));
        if (str_vector.size() < 2) {
            EDU_LOG(SEARCH_WARN, "wrong format, too few fields");
            error += 1;
            continue;
        }
        int cnt = 0;
        try {
            cnt = boost::lexical_cast<int>(str_vector[1].c_str());
        } catch (boost::bad_lexical_cast & e) {
            EDU_LOG(SEARCH_WARN, "wrong format, bad int=%s", str_vector[1].c_str());
            error += 1;
            continue;
        }
        if (2 * cnt + 2 != str_vector.size()) {
            EDU_LOG(SEARCH_WARN, "wrong format for line=%d, fields cnt out of expect=%d", line_no, cnt);
            error += 1;
            continue;
        }

        bool has_error = false;
        std::vector<KnnItem> vec;
        vec.reserve(str_vector.size());
        for (size_t i = 2; i < str_vector.size(); i += 2) {
            uint32_t item_short = 0;
            if (0 != md5id2uint32(str_vector[i], item_short)) {
                EDU_LOG(SEARCH_WARN, "wrong format, bad md5id=%s", str_vector[i].c_str());
                error += 1;
                has_error = true;
                continue;
            }
            KnnItem item;
            item.item = item_short;
            try {
                item.knn_score = boost::lexical_cast<float>(str_vector[i + 1].c_str());
            } catch (boost::bad_lexical_cast & e) {
                EDU_LOG(SEARCH_WARN, "wrong format, bad int=%s", str_vector[i + 1].c_str());
                error += 1;
                has_error = true;
                continue;
            }
            vec.emplace_back(item);
            if (_shortid2md5id.find(item_short) == _shortid2md5id.end()) {
                _shortid2md5id.insert(std::make_pair(item_short, str_vector[i]));
            }
        }
        if (has_error or vec.size() == 0) {
            continue;
        }

        _dict.insert(std::make_pair(str_vector[0], vec));
    }
    fin.close();
    return 0;
}

void VecKnnDict::get(const std::string md5id, \
        std::vector<std::pair<std::string, float> >& recall_result)
{
    recall_result.clear();
    vec_knn_dict_const_it_t it = _dict.find(md5id);
    if (it == _dict.end()) {
        return;
    }
    recall_result.reserve(it->second.size());
    for (size_t i = 0; i < it->second.size(); ++i) {
        shortid2md5id_const_it_t it1 = _shortid2md5id.find(it->second[i].item);
        if (it1 != _shortid2md5id.end()) {
            recall_result.push_back(std::make_pair(it1->second, it->second[i].knn_score));
        }
    }
}

}
}

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
