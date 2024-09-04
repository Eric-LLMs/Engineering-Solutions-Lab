#include <fstream>

#include "song_global_stat_dict.h"
#include <logger.h>

namespace demo {
namespace recommend {

// check if can reload now
int GlobalPlayStatDict::check_can_reload(const std::string & path, const std::string & conf_file)
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
int GlobalPlayStatDict::do_reload(const std::string & path, const std::string & conf_file)
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
        if (read_line.empty()){
            continue;
        }
        if (read_line.size() > 0 && read_line.c_str()[0] == '#') {
            continue;
        }
        char entity_name[1024];
        entity_name[0] = '\0';
        PlayStat play_stat;
        int ret = sscanf(read_line.c_str(), "%1000[^\t]\t%d\t%d\t%f\t%d", entity_name, 
                                                                     &play_stat.play_cnt,
                                                                     &play_stat.play_finish_cnt,
                                                                     &play_stat.finish_rate,
                                                                     &play_stat.q_call_cnt);
        if (ret != 5) {
            EDU_LOG(SEARCH_WARN, "read file %s failed for line=%s", \
                                 file.c_str(), read_line.c_str());
            error += 1;
            if (error > 5) {
                fin.close();
                return -1;
            }
        }
        _dict.insert(std::make_pair(entity_name, play_stat));
    }
    fin.close();
    return 0;
}

}
}

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
