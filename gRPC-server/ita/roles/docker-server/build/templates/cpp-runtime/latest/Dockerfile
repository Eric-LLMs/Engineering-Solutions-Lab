# c++ 运行时环境镜像

# 基础镜像
FROM {{ docker_register.ip }}/algorithms/centos:cpu

# 维护者信息
LABEL MAINTAINER  acme < acme@acme.cn>

# 设置参数
ARG ROOT_PASS="{{ docker_image_root_passwd }}"
ARG PIP_MIRROR="{{ pip_source.acme }}"

# 更新环境
RUN yum install -y gdb rsync tree gdb wget gcc gcc-c++ openssh-clients lrzsz \
	make automake cmake ncurses-devel bc zlib-devel bzip2-devel ncurses-devel \
	&& echo "root:${ROOT_PASS}" | chpasswd \
	&& ssh-keygen -A

# 外部文件
ADD libs/ /lib64/

# 编译、安装外部文件
RUN pip3 install --upgrade pip -i ${PIP_MIRROR} \
	&& pip3 install pytest==4.5.0 allure-pytest==2.8.6 supervisor==4.1.0 PyYAML==5.1.2 grpcio==1.25.0 grpcio-tools==1.25.0 Jinja2==2.10.3 protobuf==3.9.0 -i ${PIP_MIRROR}

# 容器对外暴露端口
EXPOSE 22

# 工作路径
WORKDIR /home/work

# 入口文件
ADD docker-entrypoint.sh /root/

# 启动容器时执行该命令
ENTRYPOINT ["/root/docker-entrypoint.sh"]
