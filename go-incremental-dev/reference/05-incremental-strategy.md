# 增量开发策略

## 新旧代码隔离策略

### 核心原则

1. **扩展优于修改** - 通过接口扩展新功能
2. **依赖注入解耦** - 面向接口编程
3. **适配器模式** - 隔离新旧代码交互
4. **Feature Flag** - 配置控制功能开关

---

## 1. 扩展优于修改

```go
// ✗ 错误：直接修改旧函数
func (s *OldService) Process() {
    // 修改原有逻辑...
}

// ✓ 正确：创建新实现，通过接口扩展
type Processor interface {
    Process() error
}

type NewProcessor struct {
    // 新依赖
}

func (p *NewProcessor) Process() error {
    // 新逻辑...
}
```

---

## 2. 依赖注入解耦

```go
// ✓ 正确：通过接口依赖
type Service struct {
    storage StorageInterface
}

type StorageInterface interface {
    Get(ctx context.Context, key string) ([]byte, error)
    Set(ctx context.Context, key string, val []byte) error
    Delete(ctx context.Context, key string) error
}

// 旧实现保持兼容
type LegacyStorage struct{}

func (s *LegacyStorage) Get(ctx context.Context, key string) ([]byte, error) {
    // 旧实现...
}

func (s *LegacyStorage) Set(ctx context.Context, key string, val []byte) error {
    // 旧实现...
}

func (s *LegacyStorage) Delete(ctx context.Context, key string) error {
    // 旧实现...
}

// 新实现独立开发
type NewStorage struct{}

func (s *NewStorage) Get(ctx context.Context, key string) ([]byte, error) {
    // 新实现...
}

func (s *NewStorage) Set(ctx context.Context, key string, val []byte) error {
    // 新实现...
}

func (s *NewStorage) Delete(ctx context.Context, key string) error {
    // 新实现...
}
```

---

## 3. 适配器模式对接旧代码

```go
// 适配器：包装旧服务供新代码使用
type LegacyAdapter struct {
    oldService *OldService
}

func (a *LegacyAdapter) Call() error {
    return a.oldService.OldMethod()
}

// 适配器：包装新服务供旧代码使用
type NewAdapter struct {
    newService *NewService
}

func (a *NewAdapter) LegacyMethod() error {
    return a.newService.NewMethod()
}
```

---

## 4. Feature Flag 控制

```go
type Config struct {
    features map[string]bool
}

func (c *Config) IsFeatureEnabled(name string) bool {
    return c.features[name]
}

func (s *Service) Process() error {
    if s.config.IsFeatureEnabled("new_processor") {
        return s.newProcessor.Process()
    }
    return s.oldProcessor.Process()
}
```

---

## 目录结构示例

```
project/
├── cmd/
│   └── app/
│       └── main.go
├── internal/
│   ├── legacy/           # 旧代码（不修改）
│   │   ├── service.go
│   │   └── service_test.go
│   └── features/         # 新功能目录
│       ├── myfeature/    # 新功能模块
│       │   ├── myfeature.go
│       │   ├── myfeature_test.go
│       │   ├── adapter.go      # 适配器（如需要）
│       │   └── doc.go
│       └── another/       # 另一个新功能
│           ├── another.go
│           └── another_test.go
├── pkg/                  # 公共包
│   └── httpx/
│       └── client.go
└── go.mod
```

---

## 接口设计模板

```go
// 定义接口（面向接口编程）
type FeatureInterface interface {
    DoSomething(ctx context.Context, req *Request) (*Response, error)
    Close() error
}

// 实现接口
type FeatureImpl struct {
    // 依赖项（通过构造函数注入）
    client *httpx.Client
    cache  *cachex.Cache[string, []byte]
}

func NewFeatureImpl(client *httpx.Client) *FeatureImpl {
    return &FeatureImpl{
        client: client,
        cache:  cachex.New[string, []byte](),
    }
}

func (f *FeatureImpl) DoSomething(ctx context.Context, req *Request) (*Response, error) {
    if req == nil {
        return nil, errors.New("request is nil")
    }
    // 实现...
}

func (f *FeatureImpl) Close() error {
    // 清理资源...
    return nil
}

// 确认实现接口
var _ FeatureInterface = (*FeatureImpl)(nil)
```

---

## 依赖注入示例

```go
// 服务依赖
type ServiceDependencies struct {
    Storage StorageInterface
    Cache   CacheInterface
    Logger  LoggerInterface
    Config  ConfigInterface
}

// 构造函数注入
func NewService(deps ServiceDependencies) *Service {
    return &Service{
        storage: deps.Storage,
        cache:   deps.Cache,
        logger:  deps.Logger,
        config:  deps.Config,
    }
}

// Mock 依赖（用于测试）
type MockStorage struct{}

func (m *MockStorage) Get(_ context.Context, key string) ([]byte, error) {
    return []byte("mock"), nil
}

func (m *MockStorage) Set(_ context.Context, key string, val []byte) error {
    return nil
}
```

---

## 数据迁移策略

### 1. 向后兼容的数据结构

```go
// 新增字段使用指针（可选）
type User struct {
    ID        string
    Name      string
    Email     string
    // 新增字段使用指针，兼容旧数据
    Phone     *string  `json:"phone,omitempty"`
    CreatedAt *time.Time `json:"created_at,omitempty"`
}
```

### 2. 数据库迁移脚本

```sql
-- V1: 添加新字段（可空）
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
ALTER TABLE users ADD COLUMN created_at TIMESTAMP;

-- V2: 设置默认值
UPDATE users SET phone = '' WHERE phone IS NULL;

-- V3: 添加约束
ALTER TABLE users ALTER COLUMN phone SET NOT NULL;
```

### 3. 迁移代码模板

```go
type Migrator struct {
    db *sql.DB
}

func (m *Migrator) Up(ctx context.Context) error {
    // 1. 检查迁移记录
    var count int
    err := m.db.QueryRowContext(ctx, "SELECT COUNT(*) FROM migrations WHERE version = ?", 1).Scan(&count)
    if err != nil {
        return fmt.Errorf("check migration: %w", err)
    }
    if count > 0 {
        return nil // 已迁移
    }

    // 2. 执行迁移
    tx, err := m.db.BeginTx(ctx, nil)
    if err != nil {
        return fmt.Errorf("begin transaction: %w", err)
    }
    defer tx.Rollback()

    if _, err := tx.ExecContext(ctx, "ALTER TABLE users ADD COLUMN phone VARCHAR(20)"); err != nil {
        return fmt.Errorf("add phone column: %w", err)
    }

    // 3. 记录迁移
    if _, err := tx.ExecContext(ctx, "INSERT INTO migrations (version) VALUES (?)", 1); err != nil {
        return fmt.Errorf("record migration: %w", err)
    }

    return tx.Commit()
}
```

---

## 配置管理

### 配置文件结构

```yaml
# config.yaml
app:
  name: "myapp"
  env: "production"

server:
  host: "0.0.0.0"
  port: 8080
  timeout: 30s

database:
  host: "localhost"
  port: 5432
  name: "myapp"
  max_open_conns: 25
  max_idle_conns: 5

# Feature Flags
features:
  new_processor: false  # 默认关闭
  cache_enabled: true
```

### 配置加载

```go
type Config struct {
    App      AppConfig
    Server   ServerConfig
    Database DatabaseConfig
    Features FeatureFlags
}

type FeatureFlags struct {
    NewProcessor bool
    CacheEnabled bool
}

func Load(path string) (*Config, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("read config: %w", err)
    }

    var cfg Config
    if err := yaml.Unmarshal(data, &cfg); err != nil {
        return nil, fmt.Errorf("parse config: %w", err)
    }

    return &cfg, nil
}
```

---

## 渐进式发布策略

### 1. 金丝雀发布

```go
type CanaryRouter struct {
    primary *Service
    canary  *NewService
    ratio   float64 // canary 流量比例 0.0-1.0
}

func (r *CanaryRouter) Process(ctx context.Context, req *Request) (*Response, error) {
    if rand.Float64() < r.ratio {
        return r.canary.Process(ctx, req)
    }
    return r.primary.Process(ctx, req)
}
```

### 2. A/B 测试

```go
type ABTestRouter struct {
    variantA *Service
    variantB *Service
}

func (r *ABTestRouter) Process(ctx context.Context, req *Request) (*Response, error) {
    variant := req.GetHeader("X-AB-Variant")
    switch variant {
    case "B":
        return r.variantB.Process(ctx, req)
    default:
        return r.variantA.Process(ctx, req)
    }
}
```

### 3. 回滚机制

```go
type RollbackableService struct {
    current  ServiceInterface
    previous ServiceInterface
}

func (s *RollbackableService) Process(ctx context.Context, req *Request) (*Response, error) {
    return s.current.Process(ctx, req)
}

func (s *RollbackableService) Rollback() error {
    s.current, s.previous = s.previous, s.current
    return nil
}
```
