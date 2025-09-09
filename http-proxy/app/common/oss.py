import hashlib

from app import app
from datetime import date
from retrying import retry
from typing import Any, List

@retry(stop_max_attempt_number=3)
def uploadImagesToOss(bucket, category: str, images: List[bytes], request: Any, response: Any, tm: int):
    '''
    上传相关数据到oss
    @param bucket: oss bucket object
    @param category: 数据分类
    @param images: 图片文件
    @param request: urs请求包
    @param response: urs响应包
    @param tm: urs请求耗时
    '''
    if not bucket: return

    m = hashlib.md5()
    for each in images:
        m.update(each)

    md5sum = m.hexdigest()
    app.logger.debug('image data md5 checksum: {}'.format(md5sum))
    prefix = '{}/{}/{}/{}'.format(app.config['oss']['prefix'], category, date.today().strftime('%Y-%m-%d'), md5sum)
    upload_fname = '{}.png'.format(prefix)
    upload_json_fname = '{}.json'.format(prefix)

    try:
        # 检查文件是否存在
        if not bucket.object_exists(upload_fname):
            # 上传文件到oss
            bucket.put_object(upload_fname, data)
            app.logger.debug('succeed to put oss, name={}, data size={} bytes'.format(upload_fname, len(data)))
        else:
            app.logger.debug('succeed to put oss (already), name={}, data size={} bytes'.format(upload_fname, len(data)))

        # 上传请求信息
        request.data = upload_fname.encode('utf-8') # 修改data字段，用oss中的地址替代原来的图片二进制流

        content = json.dumps({
            'request': MessageToDict(request, including_default_value_fields=True, preserving_proto_field_name=True, use_integers_for_enums=True),
            'response': MessageToDict(response, including_default_value_fields=True, preserving_proto_field_name=True, use_integers_for_enums=True),
            'tm': tm,
        }, ensure_ascii=False, indent=4)

        rtn=bucket.put_object(upload_json_fname, content)
        app.logger.debug('succeed to put oss, name={}, data size={} bytes'.format(upload_json_fname, len(content)))
    except:
        app.logger.error('exception during put oss: {}'.format(traceback.format_exc()))
        raise
