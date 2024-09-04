#
# bcloud default makefile
# more details please refer to ./.bcloud.cache/makefile.*
#
.SILENT:

#
#makefile-self location, must be always on the top!!!
#
MAKEFILE_PATH_DEFAULT := $(word $(words $(MAKEFILE_LIST)), $(MAKEFILE_LIST))
MAKEFILE_DIR_DEFAULT := $(shell cd $(dir $(MAKEFILE_PATH_DEFAULT)) && pwd)

MAKEFILE_DEAULT := 'imported'

#
#Global Configs
#
WORK_ROOT := $(shell cd $(MAKEFILE_DIR_DEFAULT)/../../.. && pwd)
GCC_PATH := /opt/compiler/gcc-4.8.2/bin

#
#import global configs
#
ifneq ($(MAKEFILE_CONFIG), 'imported')
    include $(MAKEFILE_DIR_DEFAULT)/.bcloud.cache/makefile.config
endif

.PHONEY: all clean distclean cleanall help
all: main

clean:
	echo removing $(WORK_ROOT)/bc_out/demo/\*.o ...
	find $(WORK_ROOT)/bc_out/demo -name "*.o" | xargs rm -rf
	echo removing $(WORK_ROOT)/bc_out/demo/output/bin ...
	rm -rf $(WORK_ROOT)/bc_out/demo/output/bin
	echo removing $(WORK_ROOT)/bc_out/demo/output/lib ...
	rm -rf $(WORK_ROOT)/bc_out/demo/output/lib
	echo removing $(WORK_ROOT)/bc_out/demo/output/so ...
	rm -rf $(WORK_ROOT)/bc_out/demo/output/so
	echo removing $(WORK_ROOT)/bc_out/demo/output/test ...
	rm -rf $(WORK_ROOT)/bc_out/demo/output/test
	echo removing $(WORK_ROOT)/demo/output ...
	rm -rf $(WORK_ROOT)/demo/output

distclean:
	echo removing $(WORK_ROOT)/demo/Makefile ...
	rm -rf $(WORK_ROOT)/demo/Makefile
	echo removing $(WORK_ROOT)/demo/.bcloud.cache/makefile.demo ...
	rm -rf $(WORK_ROOT)/demo/.bcloud.cache/makefile.demo
	echo removing $(WORK_ROOT)/bc_out/demo/code/demo ...
	rm -rf $(WORK_ROOT)/bc_out/demo/code/demo
	echo removing $(WORK_ROOT)/demo/output ...
	rm -rf $(WORK_ROOT)/demo/output
	echo -e '\033[32m[NOTICE]\033[0m'
	echo -e \\tplease run \'bcloud local -M\' before next \'make\'!!!

cleanall:
	echo removing $(WORK_ROOT)/bc_out ...
	rm -rf $(WORK_ROOT)/bc_out
	echo removing $(WORK_ROOT)/demo/output ...
	rm -rf $(WORK_ROOT)/demo/output
	echo removing $(WORK_ROOT)/demo/Makefile ...
	rm -rf $(WORK_ROOT)/demo/Makefile
	echo removing $(WORK_ROOT)/demo/.bcloud.cache/makefile\* ...
	rm -rf $(WORK_ROOT)/demo/.bcloud.cache/makefile*
	echo -e '\033[32m[NOTICE]\033[0m'
	echo -e \\tplease run \'bcloud local or bcloud local -M ALL\' before next \'make\'!!!

demo/base/protobuf-json: demo/base/protobuf-json_deps

demo/base/common: demo/base/common_deps

public/bvar: public/bvar_deps

public/protobuf-json: public/protobuf-json_deps

demo/bns/naming-lib: demo/bns/naming-lib_deps

lib2-64/bsl: lib2-64/bsl_deps

third-64/gflags: third-64/gflags_deps

third-64/leveldb: third-64/leveldb_deps

lib2-64/ullib: lib2-64/ullib_deps

public/common: public/common_deps

demo/base/bvar: demo/base/bvar_deps

demo/base/bsl: demo/base/bsl_deps

public/iobuf: public/iobuf_deps

demo/base/bthread: demo/base/bthread_deps

demo/base/ullib: demo/base/ullib_deps

demo/third-party/gflags: demo/third-party/gflags_deps

demo/base/demo-rpc: demo/base/demo-rpc_deps

third-64/libevent: third-64/libevent_deps

op/oped/noah/webfoot/naming-lib: op/oped/noah/webfoot/naming-lib_deps

public/bthread: public/bthread_deps

public/noah/giano-lib/release/baas-lib-c: public/noah/giano-lib/release/baas-lib-c_deps

demo/base/mcpack2pb: demo/base/mcpack2pb_deps

public/demo-rpc: public/demo-rpc_deps

demo/third-party/protobuf: demo/third-party/protobuf_deps

third-64/protobuf: third-64/protobuf_deps

public/mcpack2pb: public/mcpack2pb_deps

demo/base/iobuf: demo/base/iobuf_deps

help:
	echo -e 'all available targets of make($(MAKE_VERSION)):\n'
	echo '    all              : will compile all targets and run release.bcloud'
	echo '    no-release.bcloud: will compile all targets and not run release.bcloud'
	echo '    no-ut            : will compile all targets without ut and run release.bcloud'
	echo '    test             : will compile all targets, run ut and run release.bcloud'
	echo '    clean            : will only cleanup Intermediate files(such as .o, .so, .a, ut and bin) of main module:'
	echo '                       $(WORK_ROOT)/bc_out/demo/output/bin'
	echo '                       $(WORK_ROOT)/bc_out/demo/output/lib'
	echo '                       $(WORK_ROOT)/bc_out/demo/output/so'
	echo '                       $(WORK_ROOT)/bc_out/demo/\*.o'
	echo '                       $(WORK_ROOT)/bc_out/demo/output/test'
	echo '                       $(WORK_ROOT)/demo/output'
	echo '    distclean        : will cleanup makefile, intermediate files(such as .o, .so, .a, ut and bin) and pb.cc/pb.h idl.h/idl.cpp of main module:'
	echo '                       $(WORK_ROOT)/demo/Makefile'
	echo '                       $(WORK_ROOT)/demo/.bcloud.cache/makefile.demo_code_demo'
	echo '                       $(WORK_ROOT)/bc_out/demo/code/demo'
	echo '                       $(WORK_ROOT)/demo/output'
	echo '    cleanall         : will cleanup makefiles, intermediate files(such as .o, .so, .a, ut and bin) and pb.cc/pb.h idl.h/idl.cpp of all modules:'
	echo '                       $(WORK_ROOT)/bc_out'
	echo '                       $(WORK_ROOT)/demo/output'
	echo '                       $(WORK_ROOT)/demo/Makefile'
	echo '                       $(WORK_ROOT)/demo/.bcloud.cache/makefile*'
	echo '    help             : list all available make targets'
	echo -e '\ntargets for the compile of dependency module:'
	echo '    demo/base/demo-rpc'
	echo '    demo/base/bsl'
	echo '    demo/base/bthread'
	echo '    demo/base/bvar'
	echo '    demo/base/common'
	echo '    demo/base/iobuf'
	echo '    demo/base/mcpack2pb'
	echo '    demo/base/protobuf-json'
	echo '    demo/base/ullib'
	echo '    demo/bns/naming-lib'
	echo '    demo/third-party/gflags'
	echo '    demo/third-party/protobuf'
	echo '    lib2-64/bsl'
	echo '    lib2-64/ullib'
	echo '    op/oped/noah/webfoot/naming-lib'
	echo '    public/demo-rpc'
	echo '    public/bthread'
	echo '    public/bvar'
	echo '    public/common'
	echo '    public/iobuf'
	echo '    public/mcpack2pb'
	echo '    public/noah/giano-lib/release/baas-lib-c'
	echo '    public/protobuf-json'
	echo '    third-64/gflags'
	echo '    third-64/leveldb'
	echo '    third-64/libevent'
	echo '    third-64/protobuf'



#
#import dependency modules
#
ifneq ($(MAKEFILE_demo_CODE_demo), 'imported')
    include $(MAKEFILE_DIR_DEFAULT)/.bcloud.cache/makefile.demo_code_demo
endif
