# cpp 编译时环境镜像

# 基础镜像
FROM {{ docker_register.ip }}/algorithms/centos:cpu

# 维护者信息
LABEL MAINTAINER  acme < acme@acme.cn>

# 设置参数
ARG ROOT_PASS="{{ docker_image_root_passwd }}"
ARG PIP_MIRROR="{{ pip_source.acme }}"

# 更新环境
RUN yum update -y \
	&& yum install -y git openssl-devel zlib-devel bzip2-devel cmake flex bison python-devel libcurl-devel libtool \
	&& echo "/usr/local/lib" >> /etc/ld.so.conf \
	&& echo "root:${PASSWORD}" | chpasswd \
	&& ssh-keygen -A

# 外部文件
ADD boost_1_53_0.tar.gz gflags-2.2.1.tar.gz leveldb-1.20.tar.gz \
	ccache-3.3.5.tar.gz gflags-build.tar.gz libevent-2.1.8-stable.tar.gz protobuf-cpp-3.9.0.tar.gz cmake-3.16.tar.gz \
	c-ares-1.14.0.tar grpc-1.25.0.tar.gz fcgi2-2.4.2.tar.gz spawn-fcgi-1.6.4.tar.gz \
	/tmp/third-party/
ADD libopencc.so.1.0.0 /lib64/

# 环境变量
ENV MAC=64

# 编译、安装外部文件
RUN pip3 install --upgrade pip -i ${PIP_MIRROR} \
	&& pip3 install pytest==4.5.0 allure-pytest==2.8.6 protobuf==3.9.0 \
	grpcio==1.25.0 grpcio-tools==1.25.0 Jinja2==2.10.3 PyYAML==5.1.2 \
	-i ${PIP_MIRROR}

RUN cd /tmp/third-party/ccache-3.3.5 && ./configure && make install -j 6 \
	&& ln -s /usr/local/bin/ccache /usr/local/bin/gcc \
	&& ln -s /usr/local/bin/ccache /usr/local/bin/g++ \
	&& cd /tmp/third-party/libevent-2.1.8-stable && ./configure && make install -j 6 \
	&& cd /tmp/third-party/boost_1_53_0 && sh bootstrap.sh && ./b2 install include="/usr/local/include/python3.6m/" -j 6 \
	&& cd /tmp/third-party/protobuf-3.9.0 && ./configure && make install -j 6 \
	&& cd /tmp/third-party/gflags-2.2.1 && mv /tmp/third-party/build . && cd build && make install -j 6 \
	&& cd /tmp/third-party/leveldb-1.20 && make -j 6 && cp -rf include/leveldb /usr/local/include/ \
	&& mv out-shared/libleveldb.so* /usr/local/lib \
	&& cd /tmp/third-party/c-ares-1.14.0 && ./configure && make -j 6 && make install \
	&& export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH \
	&& ldconfig \
	&& cd /tmp/third-party/grpc-1.25.0 && make -j 6 && make install \
	&& cd /tmp/third-party/cmake-3.16.1/ && cp -rf bin doc man share /usr \
	&& ln -s /lib64/libopencc.so.2 /lib64/libopencc.so \
	&& pip3 install pyyaml jinja2 -i ${PIP_MIRROR}

RUN cd /tmp/third-party/fcgi2-2.4.2 && ./autogen.sh && ./configure && make -j 6 && make install \
	&& cd /tmp/third-party/spawn-fcgi-1.6.4 && ./configure && make -j 6 && make install

RUN rm -rf /tmp/third-party/ \
	&& ldconfig

# 入口文件
ADD docker-entrypoint.sh /root/

# 启动容器时执行该命令
ENTRYPOINT ["/root/docker-entrypoint.sh"]
