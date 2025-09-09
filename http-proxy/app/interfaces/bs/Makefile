CC = g++
PROTOC = protoc
WORKROOT = ../../
CFLAGS = -std=c++11 -O3 -Wall -g -pipe -fPIC -D__VERSION_ID__="\"1.1.1.0\""

LIB = libbsinterface.a
OBJS = bs_interface_common.pb.o bs_searcher_grpc.pb.o bs_searcher_grpc.grpc.pb.o bs_build_grpc.pb.o bs_build_grpc.grpc.pb.o

.PHONY:all
all:.release
	@echo "make all done"

.PHONY:.release
.release:$(LIB)
	@echo "build done"
	mkdir -p output/include
	mkdir -p output/lib
	cp $(LIB) output/lib
	cp *.h output/include
	@echo "end"

%.o: %.cpp
	$(CC) -c $(CFLAGS) $< -o $@

%.o: %.cc
	$(CC) -c $(CFLAGS) $< -o $@

$(LIB):$(OBJS)
	ar cr $(LIB) $^

%.grpc.pb.cc %grpc.pb.b:%.proto
	$(PROTOC) --grpc_out=. --plugin=protoc-gen-grpc=`which grpc_cpp_plugin` $<

%.pb.cc %.pb.h:%.proto
	$(PROTOC) --cpp_out=. --proto_path=. $<

clean:
	rm -f *.o *.a *~ *.pb.cc *.pb.h $(LIB)
	if [ -d output ]; then rm -rf output; fi
