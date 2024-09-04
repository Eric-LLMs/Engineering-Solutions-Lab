#include "singer_recall_dict.h"

#include <fstream>

#include <logger.h>
#include <boost/algorithm/string.hpp>
#include <boost/lexical_cast.hpp>

namespace demo {
namespace recommend {

// check if can reload now
int SingerRecallDict::check_can_reload(const std::string & path, const std::string & conf_file)
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

// 热加载数据
int SingerRecallDict::do_reload(const std::string & path, const std::string & conf_file)
{
    _dict.clear();

    std::string file = path + "/" + conf_file;
    std::ifstream fin(file.c_str());
    if (!fin) {
        EDU_LOG(SEARCH_WARN, "open file %s failed", file.c_str());
        return -1; 
    }
    std::string read_line;
    int error = 0;
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
            EDU_LOG(SEARCH_WARN, "wrong format, fields cnt out of expect=%d", cnt);
            error += 1;
            continue;
        }

        bool has_error = false;
        std::vector<RecallItem> vec;
        for (size_t i = 2; i < str_vector.size(); i += 2) {
            RecallItem item;
            item.item = str_vector[i];
            try {
                item.hot = boost::lexical_cast<int>(str_vector[i + 1].c_str());
            } catch (boost::bad_lexical_cast & e) {
                EDU_LOG(SEARCH_WARN, "wrong format, bad int=%s", str_vector[i + 1].c_str());
                error += 1;
                has_error = true;
                continue;
            }
            vec.emplace_back(item);
        }
        if (has_error) {
            continue;
        }

        _dict.insert(std::make_pair(str_vector[0], vec));
    }
    fin.close();
    return 0;
}

}
}

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
