# go-incremental-dev 辅助命令
# 用法: make <target> [GOOS=linux] [GOARCH=arm64]
# 环境变量: GOOS windows|linux|darwin, GOARCH amd64|arm64

.PHONY: help all build-knowledge build build-linux build-darwin build-win test-knowledge vet-knowledge fmt clean

# ---- 默认 ----
help:
	@echo "用法: make <target> [选项]"
	@echo ""
	@echo "构建:"
	@echo "  build-knowledge    编译 knowledge 工具（当前系统）"
	@echo "  build GOOS=linux   跨平台编译（可指定 GOOS/GOARCH）"
	@echo "  build-linux        编译到 Linux amd64"
	@echo "  build-darwin       编译到 macOS amd64"
	@echo "  build-win          编译到 Windows amd64"
	@echo ""
	@echo "检查:"
	@echo "  test-knowledge     运行 knowledge 工具测试"
	@echo "  vet-knowledge      静态检查 knowledge 工具"
	@echo "  fmt                格式化 knowledge 工具代码"
	@echo "  clean              清理构建产物"
	@echo ""
	@echo "变量: GOOS=linux|darwin|windows  GOARCH=amd64|arm64"

all: build-knowledge test-knowledge vet-knowledge

# ---- 构建当前系统 ----
build-knowledge:
	cd tools/knowledge && go build -o knowledge$(EXT) .

# ---- 跨平台编译 ----
# Go 原生支持 GOOS=linux GOARCH=amd64 go build ...
GOOS ?=
GOARCH ?=

build:
	cd tools/knowledge && GOOS=$(GOOS) GOARCH=$(GOARCH) go build -o knowledge-$(GOOS)-$(GOARCH)$(if $(filter windows,$(GOOS)),.exe,) .

# ---- 快捷跨平台 ----
build-linux:
	cd tools/knowledge && GOOS=linux GOARCH=amd64 go build -o knowledge-linux-amd64 .

build-darwin:
	cd tools/knowledge && GOOS=darwin GOARCH=amd64 go build -o knowledge-darwin-amd64 .

build-win:
	cd tools/knowledge && GOOS=windows GOARCH=amd64 go build -o knowledge-windows-amd64.exe .

# ---- 测试与检查 ----
test-knowledge:
	cd tools/knowledge && go test -v -cover .

vet-knowledge:
	cd tools/knowledge && go vet ./...

fmt:
	cd tools/knowledge && gofmt -w . && gofmt -l .

# ---- 清理 ----
clean:
	rm -f tools/knowledge/knowledge.exe
	rm -f tools/knowledge/knowledge-*
