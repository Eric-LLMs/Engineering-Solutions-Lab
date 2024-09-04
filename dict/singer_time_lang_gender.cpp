#include <fstream>

#include "singer_time_lang_gender.h"
#include <logger.h>

namespace demo {
namespace recommend {

// check if can reload now
int SingerDetailDict::check_can_reload(const std::string & path, const std::string & conf_file)
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
int SingerDetailDict::do_reload(const std::string & path, const std::string & conf_file)
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

    max_lang = max_gender = max_lang_gender = 0;
    int line_cnt = 0;
    while (std::getline(fin, read_line)) {
        if (read_line.empty()) {
            continue;
        }
        line_cnt += 1;
        if (read_line.c_str()[0] == '#') {
            if (read_line.size() >= 4 && read_line.c_str()[1] == 'm' 
                                      && read_line.c_str()[2] == 'a'
                                      && read_line.c_str()[3] == 'x') {
                int ret = sscanf(read_line.c_str(), "#max_lang=%d\tmax_gender=%d\tmax_lang_gender=%d", 
                                        &max_lang, &max_gender, &max_lang_gender);
                if (ret != 3) {
                    EDU_LOG(SEARCH_WARN, "load file %s failed: feature size get failed",
                                                                 file.c_str());
                    return -1;
                }
                continue;
            }
            if (line_cnt == 1) {
                continue;
            }
        }
        char entity_name[1024];
        entity_name[0] = '\0';
        SingerInfo singer_info;
        int ret = sscanf(read_line.c_str(), "%1000[^\t]\t%d\t%d\t%d\t%d", entity_name, 
                                                                     &singer_info.singer_year,
                                                                     &singer_info.lang,
                                                                     &singer_info.gender,
                                                                     &singer_info.lang_gender);
        if (ret != 5) {
            EDU_LOG(SEARCH_WARN, "read file %s failed for line=%d-[%s], ret=%d", \
                                 file.c_str(), line_cnt, read_line.c_str(), ret);
            error += 1;
            if (error > 5) {
                fin.close();
                return -1;
            }
        }
        singer_info.singer_year;
        _dict.insert(std::make_pair(entity_name, singer_info));
    }
    fin.close();
    if (max_lang == 0 || max_gender == 0 || max_lang_gender == 0) {
        EDU_LOG(SEARCH_WARN, "load file %s failed: feature size didn't see",
                                                    file.c_str());
        return -1;
    }
    return 0;
}

}
}

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
