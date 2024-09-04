#include <string>
#include <vector>
#include <logger.h>
#include <fstream>
#include "dual_load_common.h"
#include "dict/entity_vec.h"

namespace demo {
namespace recommend {


// 判断是否需要、以及可以重新加载数据了
int EntityVec::check_can_reload(const std::string & path, const std::string & conf_file)
{
    std::string file = path + ((path.size() > 0) ? "/" : "") + conf_file;
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
        int file_size, b, c, d, e;
        int ret = sscanf(read_line.c_str(), "#%d filesize=%d dim=%d cnt=%d name_offset=%d vec_offset=%d", 
                &update_token, &file_size, &b, &c, &d, &e);
        if (ret != 6) {
            EDU_LOG(SEARCH_WARN, "file format error(should be[#%%d filesize=%%d dim=%%d "
                        "cnt=%%d name_offset=%%d vec_offset=%%d] in first line) for file=%s", file.c_str());
            return -1;
        }
        if ((ret = check_file_size_match(file, file_size)) != 1) {
            EDU_LOG(SEARCH_WARN, "fm_model_file not ready as file size not match, ret=%d", ret);
            return ret;
        }
        if (update_token > 0) {
            return update_token;
        }
    } else {
        EDU_LOG(SEARCH_WARN, "file format error for file=%s, should start with '#' in first line", 
                file.c_str());
        return -1;
    }
    return 1;
}

// 热加载数据
int EntityVec::do_reload(const std::string & path, const std::string & conf_file)
{
    _dict.clear();
    if (_buf != NULL) {
        delete [] _buf;
        _buf = NULL;
    }
    // ===
    std::string file = path + ((path.size() > 0) ? "/" : "") + conf_file;
    std::ifstream fin(file.c_str());
    if (!fin) {
        EDU_LOG(SEARCH_WARN, "open file %s failed", file.c_str());
        return -1; 
    }
    std::string read_line;
    std::getline(fin, read_line);

    int file_size = 0;
    int dim = 0;
    int entity_cnt = 0;
    int entity_name_offset = 0;
    int entity_vec_offset = 0;
    if (read_line.size() && read_line.c_str()[0] == '#') {
        int update_token = -1; 
        int ret = sscanf(read_line.c_str(), "#%d filesize=%d dim=%d cnt=%d name_offset=%d vec_offset=%d", 
                &update_token, &file_size, &dim, &entity_cnt, &entity_name_offset, &entity_vec_offset);
        if (ret != 6) {
            EDU_LOG(SEARCH_WARN, "file format error for file=%s", file.c_str());
            return -1;
        }
        if ((ret = check_file_size_match(file, file_size)) != 1) {
            EDU_LOG(SEARCH_WARN, "fm_model_file size not match for %s, ret=%d", file.c_str(), ret);
            return -1;
        }
    } else {
        EDU_LOG(SEARCH_WARN, "file format error for file=%s, should start with '#' in first line", 
                            file.c_str());
        return -1;
    }
    if (entity_name_offset < 0 || entity_name_offset > file_size) {
        EDU_LOG(SEARCH_WARN, "wrong name_offset=%d while filesize=%d", 
                                                entity_name_offset, file_size);
        return -1;
    }
    int expect_vec_buf_size = (1 + dim) * entity_cnt * sizeof(float);
    if (entity_vec_offset < entity_name_offset || 
                (file_size - entity_vec_offset) != expect_vec_buf_size) {
        EDU_LOG(SEARCH_WARN, "bad occured: entity_vec_offset(%d) < entity_name_offset(%d) "
                             "or real_vec_buf_size(%d) != expect(%d)",
                             entity_vec_offset, entity_name_offset, 
                             file_size - entity_vec_offset, expect_vec_buf_size);
        return -1;
    }
    if (entity_cnt <= 0) {
        EDU_LOG(SEARCH_WARN, "entity_cnt(%d) > 0", entity_cnt);
        return -1;
    }
    _dim = dim;
    // === begin to read
    _buf = (float*)new float[(dim + 1)* entity_cnt];
    if (_buf == NULL) {
        EDU_LOG(SEARCH_WARN, "new failed");
        return -1;
    }
    _dict.reserve(entity_cnt * 4 / 3);
    fin.seekg(entity_name_offset);
    int cnt = 0;
    while (std::getline(fin, read_line)) {
        long offset = fin.tellg();
        _dict.insert(std::make_pair(read_line, _buf + cnt * (dim + 1)));
        cnt++;
        if (offset >= entity_vec_offset) {
            break;
        }
    }
    fin.close();
    if (cnt != entity_cnt) {
        EDU_LOG(SEARCH_WARN, "read_entity_cnt(%d) != expect_entity_cnt(%d)", cnt, entity_cnt);
        delete [] _buf;
        return -1;
    }

    FILE * fp = fopen(file.c_str(), "rb");
    if (fp == NULL) {
        EDU_LOG(SEARCH_WARN, "how could it be failed: open failed");
        delete [] _buf;
        return -1;
    }
    if (0 != fseek(fp, entity_vec_offset, 0)) {
        fclose(fp);
        delete [] _buf;
        EDU_LOG(SEARCH_WARN, "fseek failed");
        return -1;
    }
    int read_len = fread(_buf, sizeof(float), (dim + 1)* entity_cnt, fp);
    if (read_len != (dim + 1)* entity_cnt) {
        delete [] _buf;
        EDU_LOG(SEARCH_WARN, "read failed, read_cnt=%d, expect=%d\n", 
                                read_len, (dim + 1)* entity_cnt);
        fclose(fp);
        return -1;
    }
    fclose(fp);
    return 0;
}

}
}

/* vim: set expandtab ts=4 sw=4 sts=4 tw=100: */
