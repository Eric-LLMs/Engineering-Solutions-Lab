#include <fstream>
#include <math.h>

#include "song_name_time.h"
#include <logger.h>

namespace demo {
namespace recommend {

// check if can reload now
int SongNameTimeDict::check_can_reload(const std::string & path, const std::string & conf_file)
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
int SongNameTimeDict::do_reload(const std::string & path, const std::string & conf_file)
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

    int line_cnt = 0;
    while (std::getline(fin, read_line)) {
        if (read_line.empty()) {
            continue;
        }
        if (line_cnt == 0 && read_line.c_str()[0] == '#') {
            continue;
        }
        line_cnt += 1;
        char entity_name[1024];
        entity_name[0] = '\0';
        SongNameInfo song_name_info;
        int ret = sscanf(read_line.c_str(), "%1000[^\t]\t%ld\t%ld", entity_name, 
                            &song_name_info.year_hottest, &song_name_info.year_earliest);
        if (ret != 3) {
            EDU_LOG(SEARCH_WARN, "read file %s failed for line=%d/[%s], ret=%d", \
                                 file.c_str(), line_cnt, read_line.c_str(), ret);
            error += 1;
            if (error > 5) {
                fin.close();
                return -1;
            }
        }
        _dict.insert(std::make_pair(entity_name, song_name_info));
    }
    fin.close();
    return 0;
}

}
}

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
