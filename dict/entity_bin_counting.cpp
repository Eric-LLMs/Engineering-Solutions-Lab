#include <logger.h>
#include <fstream>
#include <boost/algorithm/string.hpp>
#include <boost/lexical_cast.hpp>

#include "entity_bin_counting.h"

namespace demo {
namespace recommend {

int EntityBinCountingDict::check_can_reload(const std::string& path, const std::string& conf_file) {
    std::string file = path + "/" + conf_file;
    std::ifstream fin(file.c_str());
    if (!fin) {
        EDU_LOG(SEARCH_WARN, "open file %s failed", file.c_str());
        return -1;
    }
    return 1;
}

int EntityBinCountingDict::do_reload(const std::string& path, const std::string& conf_file) {
    _dict.clear();
    //std::cout << "base ranker load file to entity history" << std::endl;
    std::string file_name = path + '/' + conf_file;
    std::ifstream fin(file_name.c_str());
    if (!fin) {
        EDU_LOG(SEARCH_FATAL, "open file failed: filename=%s", file_name.c_str());
        return -1;
    }
    std::string line;
    int index = 0;
    int err_cnt = 0;
    while (std::getline(fin, line)) {
        index++;
        if (line.size() == 0 || line[0] == '#') {
            continue;
        }
        std::vector<std::string> elems;
        boost::split(elems, line, boost::is_any_of("|"));
        if (elems.size() != 4) {
            EDU_LOG(SEARCH_WARN, "file=%s format error, line: %d", file_name.c_str(), index);
            err_cnt += 1;
            if (err_cnt > 5) {
                EDU_LOG(SEARCH_FATAL, "file=%s, format error exceed 5", file_name.c_str());
                return -1;
            }
            continue;
        }
        try {
            bin_counting_t bin_counting(boost::lexical_cast<float>(elems[1]), boost::lexical_cast<float>(elems[2]), boost::lexical_cast<float>(elems[3]));
            _dict.insert(std::make_pair(elems[0], bin_counting));
        } catch (const boost::bad_lexical_cast &) {
            EDU_LOG(SEARCH_WARN, "boost lexical cast conversion failed. filename=%s", file_name.c_str());
        }
    }
    fin.close();
    return 0;
}

}
}
