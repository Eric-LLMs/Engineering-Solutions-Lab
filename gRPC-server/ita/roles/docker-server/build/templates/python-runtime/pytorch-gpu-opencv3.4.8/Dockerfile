# python torch 运行时环境镜像

# 基础镜像
FROM {{ docker_register.ip }}/algorithms/centos:gpu

# 维护者信息
LABEL MAINTAINER  acme < acme@acme.cn>

# 设置参数
ARG ROOT_PASS="{{ docker_image_root_passwd }}"
ARG PIP_MIRROR="{{ pip_source.acme }}"

# 更新环境
RUN yum install -y rsync tree wget openssh-clients lrzsz \
	make automake cmake ncurses-devel bc zlib-devel bzip2-devel ncurses-devel libSM libXrender libXext \
	&& echo "root:${ROOT_PASS}" | chpasswd \
	&& ssh-keygen -A

ADD libs/ /lib64/

# 编译、安装外部文件
RUN pip3 install --upgrade pip -i ${PIP_MIRROR} \
	&& pip3 install pytest==4.5.0 allure-pytest==2.8.6 supervisor==4.1.0 Flask==1.1.1 protobuf==3.9.0 \
	grpcio==1.25.0 grpcio-tools==1.25.0 Jinja2==2.10.3 pandas==0.25.1 PyYAML==5.1.2 ansible==2.9.1 \
	Cython==0.29.14 torch==1.2.0 torchvision==0.4.0 -i ${PIP_MIRROR} \
	&& rm /usr/lib64/libstdc++.so.6 && ln -s /lib64/libstdc++.so.6.0.25 /usr/lib64/libstdc++.so.6

# 容器对外暴露端口
EXPOSE 22

# 工作路径
WORKDIR /home/work

# 入口文件
ADD docker-entrypoint.sh /root/

# 启动容器时执行该命令
ENTRYPOINT ["/root/docker-entrypoint.sh"]
