SUB_DIRS 		= $(shell find ./ -maxdepth 3 -type d)
SRCS_PROTO 		= $(foreach dir, $(SUB_DIRS), $(wildcard $(dir)/*.proto))
GRPC_PY 		= $(SRCS_PROTO:.proto=_pb2_grpc.py)
GRPC_PY_PB2 	= $(SRCS_PROTO:.proto=_pb2.py)
PROTOC_PY		= python3 -m grpc_tools.protoc

all: $(GRPC_PY) $(GRPC_PY_PB2)
	@echo Done

python: $(GRPC_PY) $(GRPC_PY_PB2)

%_pb2.py %_pb2_grpc.py:%.proto
	$(PROTOC_PY) \
	--python_out=$(dir $<) \
	--grpc_python_out=$(dir $<) \
	--proto_path=$(dir $<) \
	-I. \
	$<

clean:
	@rm -rf $(GRPC_PY) $(GRPC_PY_PB2)
	@echo "DONE"
