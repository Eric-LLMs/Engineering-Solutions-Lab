# python3 -m grpc_tools.protoc --python_out=${__dir__} --grpc_python_out=${__dir__} --proto_path=${__dir__} -I${__dir__} ${ALL_PROTO}

PROTOS 			= $(shell find . -type f -name "*.proto")

PROTOC_PY		= python3 -m grpc_tools.protoc
GRPC_PY 		= $(PROTOS:.proto=_pb2_grpc.py)
GRPC_PY_PB2 	= $(PROTOS:.proto=_pb2.py)

all: python

python: $(GRPC_PY) $(GRPC_PY_PB2)

%_pb2.py %_pb2_grpc.py:%.proto
	$(PROTOC_PY) \
	--python_out=. \
	--grpc_python_out=. \
	--proto_path=. \
	-I. \
	$<

clean:
	@rm -rf $(GRPC_PY) $(GRPC_PY_PB2)
	@echo "DONE"
