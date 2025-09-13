gRPC-server

# 新添加服务配置在目录 gRPC-server/ita/inventory/services 下面
# 安装虚拟环境
```bash
# 如果是新安装conda，需要激活。
conda create -n gRPC_server_py36 python=3.6
conda activate gRPC_server_py36_py36
```

# 下载项目
```bash
git@192.168.1.78:model-services/live-comments-analysis.git
cd live-comments-analysis
# 下载依赖项目
git submodule update --init
cd framework
git submodule update --init
# 获取数据和模型
cd bin
sh fetch-data.sh
```

# 安装依赖
```bash
# 设置清华源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pip -U
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

conda install grpcio-tools
# 或者
pip3 install grpcio-tools

pip install -r bin/requirements.txt
```

# 启动服务
```bash
sh bin/startup.sh
# 客户端测试
cd test
python client.py
```