---
name: go-full-dev-workflow
description: |
  Go 项目完整开发工作流：项目治理 → 需求分析 → 代码实现 → 测试生成 → 全面审查 → API 文档 → 服务验证。
  适用于 Go HTTP 项目的新功能开发、代码重构后验证、Bug 修复后测试。

workflow:
  stages:
    - stage: governance
      name: 项目治理
      skills:
        - go-project-rules
      description: 初始化、进度同步、README 联动

    - stage: preparation
      name: 准备与文档
      skills:
        - feature-development-workflow
        - doc-generator

    - stage: implementation
      name: 代码实现
      description: 遵循 Go 规范编写代码
      
    - stage: testing
      name: 测试生成
      skills:
        - test-generator

    - stage: review
      name: 质量审查
      skills:
        - error-handling-reviewer
        - go-concurrency-reviewer
        - dependency-reviewer
        - performance-reviewer
        - security-reviewer
        - database-reviewer
        - logging-reviewer
        - context-propagation-reviewer
        - api-design-reviewer

    - stage: documentation
      name: 文档生成
      skills:
        - go-api-doc-generator

    - stage: verification
      name: 验证与部署
      actions:
        - go build
        - go test -race
        - service startup
        - api verification
---

# Go 项目完整开发工作流

## 概览

本工作流整合 13 个专项技能，覆盖 Go 项目开发全生命周期：

```
阶段零：项目治理
└── go-project-rules             (初始化、进度同步、README 联动)

阶段一：准备与文档
├── feature-development-workflow  (需求分析、任务拆解)
└── doc-generator                  (项目文档、结构说明)

阶段二：代码实现
└── 遵循开发规范 + doc-generator

阶段三：测试生成
└── test-generator                 (单元测试、Mock)

阶段四：质量审查
├── error-handling-reviewer        (错误处理)
├── go-concurrency-reviewer        (并发安全)
├── dependency-reviewer             (依赖管理)
├── performance-reviewer            (性能审查)
├── security-reviewer               (安全审查)
├── database-reviewer               (数据库)
├── logging-reviewer                (日志规范)
├── context-propagation-reviewer    (Context 链路)
└── api-design-reviewer             (API 设计)

阶段五：文档生成
└── go-api-doc-generator           (OpenAPI/Postman/curl)

阶段六：验证部署
├── go build                        (编译)
├── go test -race                   (竞态检测)
├── go run                          (启动)
└── API 验证                        (端点测试)
```

## 详细步骤

### 阶段零：项目治理 (go-project-rules)

**目标**: 确保项目一致性、进度可视化和规范执行

#### 0.1 对话启动强制初始化

**目标**: 每次新对话开始时，必须按顺序读取项目上下文

**操作**:
```bash
# 1. 读取 README.md - 掌握项目架构、技术栈、目录结构
# 2. 读取 project.md - 获取当前进度状态
```

**输出格式**:
> 已同步项目上下文，当前进度：Phase X 进行中 / 已完成，下一步为 Step Y

**缺失处理**:
- 若 `README.md` 或 `project.md` 缺失，必须立即提示并建议补全

---

#### 0.2 项目进度强制同步

**目标**: project.md 是唯一进度信源

**进度看板结构**:
```markdown
Phase N: 名称
  - [ ] Step X: 描述
  - [ ] Step Y: 描述
```

**强制规则**:
- Phase/Step 完成后必须立即将 `- [ ]` 改为 `- [x]`
- 多个子任务仅当全部完成才能勾选
- 进度更新后输出："`project.md` 已同步，当前进度：……"

---

#### 0.3 架构变更与 README 联动

**目标**: 架构调整必须同步更新文档

**必须同步更新 README.md 的场景**:
- 新增/删除模块或服务
- 调整目录结构（`pkg/`、`internal/` 拆分）
- 新增/修改 API 端点
- 引入新的外部依赖
- 改变启动命令、配置方式、环境变量

**更新章节**:
- 架构介绍
- 目录结构
- API 列表
- 部署说明

---

#### 0.4 提交前 README 一致性检查

**目标**: 提交前确保文档与代码一致

**提交前必须检查**:
- [ ] 新增的对外接口是否在 API 概览中体现
- [ ] 配置项或环境变量是否反映到配置说明
- [ ] 模块职责是否与实际代码结构一致

**检查不通过**: 禁止提交，必须修正后重检

---

#### 0.5 AI 行为自检

**目标**: 每次回复前判断是否触发规则

| 检测类型 | 触发动作 |
|----------|----------|
| 阶段完成 | 触发进度同步 + 工作流 |
| 架构调整 | 触发 README 更新 |
| API 修改 | 触发即时验证 |
| 准备提交 | 触发 README 一致性检查 |

**不确定时**: 主动提示用户确认

---

#### 0.6 规则生效与维护

- 本规则对所有 CodeBuddy 实例强制生效
- 规则变更后下一次对话生效
- 建议 CI 检查：`project.md` 进度与 tag/release 对应

---

### 阶段一：准备与文档

#### 1.1 feature-development-workflow - 需求分析

**目标**: 澄清需求，拆解任务

**操作**:
```bash
# 触发技能
"use feature-development-workflow"
"分析需求"
"拆解任务"
```

**输出**: 任务清单、设计文档

---

#### 1.2 doc-generator - 项目文档

**目标**: 分析项目结构，生成文档

**操作**:
```bash
"use doc-generator"
"分析项目结构"
"生成 README"
```

**输出**: 项目文档 (README.md, ARCHITECTURE.md)

---

### 阶段二：代码实现

**原则**:
- 遵循 Go 编码规范（gofmt、命名约定）
- 每个导出函数必须有 GoDoc 注释
- 错误处理遵循 "errors are values" 哲学
- Context 贯穿整个调用链路
- 资源必须正确关闭

**代码模板**:

```go
// ProcessRequest 处理用户请求
//
// AI-Usage: 用于处理业务逻辑的入口函数
//
// 参数:
//   - ctx: 上下文，用于超时控制和取消
//   - req: 请求参数
//
// 返回:
//   - 成功时返回处理结果
//   - 失败时返回错误
func ProcessRequest(ctx context.Context, req *Request) (*Response, error) {
    // 1. 参数校验
    if req == nil {
        return nil, ErrInvalidRequest
    }

    // 2. 创建带超时的上下文
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    // 3. 执行逻辑
    result, err := doProcess(ctx, req)
    if err != nil {
        return nil, fmt.Errorf("process request: %w", err)
    }

    // 4. 日志记录
    log.Info("request processed",
        "request_id", req.ID,
        "duration", time.Since(start),
    )

    return result, nil
}
```

---

### 阶段三：测试生成

#### 3.1 test-generator - 测试生成

**目标**: 生成完整的测试套件

**触发**:
```
"use test-generator"
"生成单元测试"
"生成边界测试"
```

**生成测试类型**:

| 类型 | 覆盖内容 | 命名 |
|------|----------|------|
| 正常路径 | 有效输入、预期输出 | TestFunctionName_Valid |
| 边界情况 | nil、空值、极端值 | TestFunctionName_EdgeCases |
| 错误路径 | 异常处理、无效输入 | TestFunctionName_Errors |
| 并发安全 | goroutine 竞争 | TestFunctionName_Concurrent |

**测试结构**:
```go
func TestProcessRequest(t *testing.T) {
    tests := []struct {
        name    string
        input   *Request
        want    *Response
        wantErr error
    }{
        {
            name:    "valid request",
            input:   &Request{ID: "1", Name: "test"},
            want:    &Response{ID: "1", Status: "ok"},
            wantErr: nil,
        },
        {
            name:    "nil request",
            input:   nil,
            want:    nil,
            wantErr: ErrInvalidRequest,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ProcessRequest(context.Background(), tt.input)
            if !errors.Is(err, tt.wantErr) {
                t.Errorf("ProcessRequest() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

---

### 阶段四：质量审查

执行以下审查技能，按顺序进行：

#### 4.1 error-handling-reviewer

**审查范围**:
- [ ] error 值是否被正确检查
- [ ] panic/recover 使用是否合理
- [ ] 错误是否正确传播（%w）
- [ ] 参数校验是否完整

#### 4.2 go-concurrency-reviewer

**审查范围**:
- [ ] Map 并发读写保护
- [ ] Goroutine 退出机制
- [ ] WaitGroup 计数准确性
- [ ] Channel 关闭安全性
- [ ] 闭包捕获循环变量

#### 4.3 dependency-reviewer

**审查范围**:
- [ ] 依赖必要性（标准库优先）
- [ ] 版本锁定检查
- [ ] 传递依赖分析
- [ ] 漏洞扫描

#### 4.4 performance-reviewer

**审查范围**:
- [ ] 超时设置
- [ ] 资源关闭（defer Close）
- [ ] 内存分配优化
- [ ] sync.Pool 使用

#### 4.5 security-reviewer

**审查范围**:
- [ ] 敏感信息硬编码
- [ ] SQL/命令注入
- [ ] 认证授权
- [ ] 依赖漏洞

#### 4.6 database-reviewer

**审查范围**:
- [ ] 连接池配置
- [ ] 事务正确性
- [ ] N+1 查询
- [ ] SQL 注入防护

#### 4.7 logging-reviewer

**审查范围**:
- [ ] 日志级别使用
- [ ] 敏感信息脱敏
- [ ] 结构化日志
- [ ] 上下文完整性

#### 4.8 context-propagation-reviewer

**审查范围**:
- [ ] Context 链路完整性
- [ ] 超时设置合理性
- [ ] 取消信号处理
- [ ] Header 传播

#### 4.9 api-design-reviewer

**审查范围**:
- [ ] RESTful 规范
- [ ] HTTP 状态码
- [ ] 命名一致性
- [ ] 版本控制

---

### 阶段五：文档生成

#### 5.1 go-api-doc-generator - API 文档

**目标**: 生成完整的 API 文档

**触发**:
```
"use go-api-doc-generator"
"生成 OpenAPI 文档"
"生成 Postman 集合"
```

**生成内容**:

| 文件 | 格式 | 用途 |
|------|------|------|
| `openapi.yaml` | YAML | OpenAPI 3.0 规范 |
| `postman_collection.json` | JSON | Postman 导入 |
| `curl_commands.sh` | Shell | 命令行测试 |
| `API_REFERENCE.md` | Markdown | 参考文档 |

---

### 阶段六：验证与部署

#### 6.1 编译检查

```bash
# 格式化检查
gofmt -l .

# 静态分析
go vet ./...

# 编译
go build -o service ./cmd/...
```

#### 6.2 测试验证

```bash
# 单元测试 + 覆盖率
go test -cover ./...

# 竞态检测
go test -race ./...

# 漏洞扫描
go install golang.org/x/vuln/cmd/govulncheck@latest
govulncheck ./...
```

#### 6.3 服务启动

```bash
# 环境准备
export SERVICE_PORT=8080
export LOG_LEVEL=debug

# 启动服务
go run ./cmd/... -port $SERVICE_PORT &
SERVICE_PID=$!
sleep 3
```

#### 6.4 API 验证

```bash
# 健康检查
curl -s http://localhost:8080/health | jq .

# 端点测试
curl -s http://localhost:8080/api/v1/resource | jq .

# 验证清单
test_endpoint GET /health 200
test_endpoint GET /api/v1/resource 200
test_endpoint POST /api/v1/resource 201
test_endpoint GET /api/v1/resource/999 404
```

---

## 自动化脚本

### 完整工作流脚本

```bash
#!/bin/bash
# go-full-workflow.sh

set -e

PROJECT_DIR=${1:-"."}
PORT=${2:-"8080"}

echo "=== Go 完整开发工作流 ==="

cd "$PROJECT_DIR"

# 阶段一：编译检查
echo "[1/6] 编译检查..."
go build ./... || exit 1

# 阶段二：静态分析
echo "[2/6] 静态分析..."
go vet ./...

# 阶段三：测试
echo "[3/6] 测试 + 竞态检测..."
go test -race -cover ./...

# 阶段四：文档生成
echo "[4/6] 生成 API 文档..."
if [ -d "docs/api" ]; then
    go run ./tools/openapi-gen.go
fi

# 阶段五：启动服务
echo "[5/6] 启动服务 (端口 $PORT)..."
go run ./cmd/... -port $PORT &
SERVICE_PID=$!
sleep 3

# 阶段六：API 验证
echo "[6/6] API 验证..."
curl -s http://localhost:$PORT/health | grep -q "ok" && echo "✓ 健康检查通过"

# 清理
kill $SERVICE_PID 2>/dev/null || true

echo "=== 工作流完成 ==="
```

---

## 故障排除

### 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 编译失败 | 依赖缺失 | `go mod tidy` |
| 测试失败 | 逻辑错误 | 检查测试用例 |
| 竞态检测失败 | 并发不安全 | 使用 mutex/channel |
| API 验证失败 | 服务未启动 | 启动服务后重试 |

### 调试命令

```bash
# 详细测试
go test -v ./...

# 竞态检测
go test -race ./...

# 内存分析
go test -memprofile=mem.prof ./...
go tool pprof mem.prof

# 逃逸分析
go build -gcflags="-m" ./...
```

---

## 输出清单

工作流完成后，应生成以下文件：

```
project/
├── README.md                   # 项目文档
├── ARCHITECTURE.md            # 架构文档
├── docs/
│   └── api/
│       ├── openapi.yaml       # OpenAPI 规范
│       ├── postman_collection.json
│       ├── curl_commands.sh
│       └── API_REFERENCE.md
├── *_test.go                  # 测试文件
└── WORKFLOW_OUTPUT.md         # 执行报告
```
