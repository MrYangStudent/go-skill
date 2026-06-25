# go-incremental-dev 辅助命令
# 用法: make <target> [GOOS=linux] [GOARCH=arm64]
# 默认编译当前操作系统，支持跨平台

.PHONY: all build-knowledge build test-knowledge vet-knowledge clean

all: build-knowledge test-knowledge vet-knowledge

# ---- 默认：编译当前系统 ----
build-knowledge:
	cd tools\knowledge && go build -o knowledge.exe .

# ---- 跨平台编译 ----
# 用法: make build GOOS=linux          (Linux amd64)
#       make build GOOS=darwin         (macOS amd64)
#       make build GOOS=windows        (Windows amd64)
#       make build GOOS=linux GOARCH=arm64  (Linux arm64)
GOOS ?= windows
GOARCH ?= amd64
EXT := $(if $(filter windows,$(GOOS)),.exe,)
build:
	cd tools\knowledge && set GOOS=$(GOOS)&& set GOARCH=$(GOARCH)&& go build -o knowledge-$(GOOS)-$(GOARCH)$(EXT) .

# ---- 快捷跨平台 ----
build-linux:
	$(MAKE) build GOOS=linux GOARCH=amd64

build-darwin:
	$(MAKE) build GOOS=darwin GOARCH=amd64

build-win:
	$(MAKE) build GOOS=windows GOARCH=amd64

# ---- 测试与检查 ----
test-knowledge:
	cd tools\knowledge && go test -v -cover .

vet-knowledge:
	cd tools\knowledge && go vet ./...

# ---- 清理 ----
clean:
	-del /Q tools\knowledge\knowledge.exe 2>nul
	-del /Q tools\knowledge\knowledge-*.exe 2>nul
	-del /Q tools\knowledge\knowledge-* 2>nul
