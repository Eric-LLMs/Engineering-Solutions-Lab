# redis镜像

# 基础镜像
FROM redis:latest

# 维护者信息
LABEL MAINTAINER  acme < acme@acme.cn>

# 外部文件
ADD redis_exporter /usr/local/bin/

# 容器对外暴露端口
EXPOSE 22

# 启动容器时执行该命令。由于自定义启动的考虑，该文件在镜像中并不存在，需要run的时候临时指定
ENTRYPOINT ["/root/docker-entrypoint.sh"]
