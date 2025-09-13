# centos环境(gpu)镜像

# 基础镜像
FROM nvidia/cuda:10.0-cudnn7-runtime-centos7

# 维护者信息
LABEL MAINTAINER  acme < acme@acme.cn>

# 设置参数
ARG ROOT_PASS="{{ docker_image_root_passwd }}"

# 更新环境
RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
	&& sed -i -e 's/override_install_langs/#override_install_langs/' /etc/yum.conf \
    && yum update -y \
    && yum install -y file zip openssh-server openssl openssl-devel lrzsz \
    man which net-tools psmisc tree lftp telnet zlib-devel bzip2-devel rsync \
    ncurses-devel wget expect crontabs bc passwd util-linux-user cracklib-dicts \
    gcc gcc-c++ make langpacks-zh_CN glibc-langpack-en xz-devel pcre-devel automake \
    sudo bzip2 unzip sshpass ntpdate python-devel python-setuptools sqlite-devel python36 \
    && yum reinstall -y glibc-common \
    && echo "/usr/local/lib" >> /etc/ld.so.conf && echo "/usr/local/lib64" >> /etc/ld.so.conf && ldconfig \
    && echo "root:${ROOT_PASS}" | chpasswd \
    && ssh-keygen -A

# 外部文件
ADD vim-8.0.1428.tar.gz the_silver_searcher-2.2.0.tar.gz Python-3.6.5.tgz \
    /tmp/third-party/

# 编译、安装外部文件
RUN ntpdate us.pool.ntp.org \
    && cd /tmp/third-party/vim-8.0.1428 && ./configure --with-features=huge --enable-multibyte \
    --enable-pythoninterp=yes --enable-gui=gtk2 --enable-cscope \
    && make install -j 4 \
    && cd /tmp/third-party/Python-3.6.5 && ./configure --enable-optimizations --with-ssl && make install -j 4 \
    && cd /tmp/third-party/the_silver_searcher-2.2.0 && ./build.sh && make install \
    && rm -rf /tmp/third-party/ \
    && ln -sf /usr/local/bin/python3 /usr/bin/python3 \
    && echo "alias ll='ls -l'" >> ~/.bashrc \
    && echo "alias vi='vim'" >> ~/.bashrc \
	&& echo "alias rz='rz -be'" >> ~/.bashrc \
	&& echo "alias sz='sz -be'" >> ~/.bashrc \
    && echo 'export LC_ALL=en_US.UTF-8' >> ~/.bashrc \
    && echo 'export LANG=en_US.UTF-8' >> ~/.bashrc

# 容器对外暴露端口
EXPOSE 22

# 入口文件
ADD docker-entrypoint.sh /root
ADD filebeat-7.7.0.tar.gz /root

RUN mv /root/filebeat-7.7.0-linux-x86_64 /root/filebeat

# 启动容器时执行该命令
ENTRYPOINT ["/root/docker-entrypoint.sh"]
