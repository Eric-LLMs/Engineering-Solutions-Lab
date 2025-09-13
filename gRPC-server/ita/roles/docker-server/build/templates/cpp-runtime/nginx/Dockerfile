# nginx/c++ 运行时环境镜像

# 基础镜像
FROM {{ docker_register.ip }}/algorithms/cpp-runtime:latest

# 维护者信息
LABEL MAINTAINER  acme < acme@acme.cn>

# 设置参数
ARG ROOT_PASS="{{ docker_image_root_passwd }}"

# 更新环境
RUN yum install -y libtool

# 外部文件
ADD nginx-1.6.2.tar.gz fcgi2-2.4.2.tar.gz spawn-fcgi-1.6.4.tar.gz /tmp/third-party/

# 编译、安装外部文件
RUN cd /tmp/third-party/nginx-1.6.2 && ./configure && make -j 4 && make install \
    && cd /tmp/third-party/fcgi2-2.4.2 && ./autogen.sh && ./configure && make -j 6 && make install \
	&& cd /tmp/third-party/spawn-fcgi-1.6.4 && ./configure && make -j 6 && make install \
    && rm -rf /tmp/third-party \
    && ldconfig

# 容器对外暴露端口
EXPOSE 22

# 工作路径
WORKDIR /home/work

# 入口文件
ADD docker-entrypoint.sh /root/

# 启动容器时执行该命令
ENTRYPOINT ["/root/docker-entrypoint.sh"]
