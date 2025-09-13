gRPC-server

# 1. Setup & Run

### Create a virtual environment
```bash
# 如果是新安装conda，需要激活。
conda create -n gRPC_server_py36 python=3.6
conda activate gRPC_server_py36_py36
```

### Clone the project 
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

### Install dependencies 
```bash
# 设置清华源
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple pip -U
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

conda install grpcio-tools
# 或者
pip3 install grpcio-tools

pip install -r bin/requirements.txt
```

### Start the server
```bash
sh bin/startup.sh
# 客户端测试
cd test
python client.py
```

# 2. Adding a New Service   
### To add a new gRPC service implementation, follow these steps:
- Create a new service implementation under the directory:
``` 
  gRPC-server/ita/inventory/services/  
```
- Add a configuration file for the new service in the same directory. This configuration will define how the service is registered and started within the gRPC server framework.
- Restart the server to load the newly added service. 