#!/usr/bin/env python3
#coding=utf-8
# 服务入口代码

import sys
import traceback

from pathlib import Path

__dir__ = Path(__file__).resolve().parent
__base__ = __dir__.parent
__conf__ = __base__.joinpath('conf')
__log__ = __base__.joinpath('log')

sys.path.append(str(__base__))

if __name__ == '__main__':
    rtn = 0

    if not __log__.exists():
        __log__.mkdir()

    from framework import app, ErrCode, FrameworkException

    # app
    try:
        app.run()
    except FrameworkException as ex:
        if ex.errcode == ErrCode.FAILED:
            rtn = -1
        else:
            rtn = ex.errcode.value
    except KeyboardInterrupt:
        app.logger.error('keyboard interrupt!!!')
        rtn = -1
    except Exception:
        app.logger.critical('unknown exception: {}'.format(traceback.format_exc()))
        rtn = -1
    finally:
        sys.exit(rtn)
