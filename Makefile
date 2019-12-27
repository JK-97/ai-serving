PROTOC_VER=3.10.0
PROTOC_LINK=https://github.com/protocolbuffers/protobuf/releases/download/v$(PROTOC_VER)
PROTOC_SRC=protoc-$(PROTOC_VER)-linux-x86_64.zip

GRPCIO_VER=1.24.3
GRPCIO_TOOLS_VER=1.24.3

DIR=src/serving/interface

.PHONY: protoc message-linux-amd64

protoc:
	# https://grpc.io/docs/quickstart/python/
	python3 -m pip install grpcio==$(GRPCIO_VER)
	python3 -m pip install grpcio-tools==$(GRPCIO_TOOLS_VER)

message-linux-amd64:
	srcs="backend connectivity inference model exchange"; \
	for proto_file in common $$srcs; do \
		echo "building:" $(DIR)/$$proto_file.proto; \
		python3 -m grpc_tools.protoc -I$(DIR) --python_out=$(DIR) --grpc_python_out=$(DIR) $(DIR)/$$proto_file.proto; \
		cmd="sed -i 's/$${proto_file}_pb2/serving.interface.&/' $(DIR)/$${proto_file}_pb2_grpc.py"; \
		eval $$cmd; \
	done; \
	for proto_file in $$srcs; do \
		echo "updating:" $(DIR)/$$proto_file.proto; \
		cmd="sed -i 's/common_pb2/serving.interface.&/' $(DIR)/$${proto_file}_pb2.py"; \
		eval $$cmd; \
		cmd="sed -i 's/common_pb2/serving.interface.&/' $(DIR)/$${proto_file}_pb2_grpc.py"; \
		eval $$cmd; \
	done; \
	echo "updating:" $(DIR)/backend.proto; \
	cmd="sed -i 's/model_pb2/serving.interface.&/' $(DIR)/backend_pb2.py"; \
	eval $$cmd; \
	cmd="sed -i 's/model_pb2/serving.interface.&/' $(DIR)/backend_pb2_grpc.py"; \
	eval $$cmd

