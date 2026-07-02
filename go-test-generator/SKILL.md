---
name: go-test-generator
description: >
  Go 测试生成技能。当用户要求为代码生成测试、编写单元测试、创建 test 文件、
  或请求生成 table-driven tests 时触发。专门用于生成完整的、可运行的测试套件，
  包含正常路径、边界情况和错误路径测试。
triggers:
  - 生成测试
  - 写单元测试
  - 测试生成员
  - table-driven tests
  - 并发测试
  - race condition 测试
---

# 测试生成专员 (Test Generator)

## 技能定位

Go 测试专家，擅长生成高质量、可维护的测试套件。遵循 Go 官方测试最佳实践。

## 测试覆盖要求

### 1. 正常路径测试
- 基本功能验证
- 多种输入组合
- 预期输出准确性

### 2. 边界情况测试
- nil 值
- 零值（空字符串、0、空切片）
- 空结构体
- 极端值（最大值、最小值）

### 3. 错误路径测试
- 无效输入
- 错误条件
- 错误传播验证

### 4. 并发安全测试
- race condition 检测
- 并发读写场景
- `go test -race` 兼容

## 测试模板

### 基础函数测试

```go
package mathutil

import "testing"

// Test_Add_Normal 测试加法正常路径
func Test_Add_Normal(t *testing.T) {
	tests := []struct {
		name     string
		a        int
		b        int
		expected int
	}{
		{"正数相加", 1, 2, 3},
		{"负数相加", -1, -2, -3},
		{"零值", 0, 5, 5},
		{"大数相加", 1000000, 2000000, 3000000},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := Add(tt.a, tt.b)
			if result != tt.expected {
				t.Errorf("Add(%d, %d) = %d; want %d", tt.a, tt.b, result, tt.expected)
			}
		})
	}
}

// Test_Add_EdgeCases 测试加法边界情况
func Test_Add_EdgeCases(t *testing.T) {
	tests := []struct {
		name  string
		a     int
		b     int
		check func(int) bool
	}{
		{"零加零", 0, 0, func(r int) bool { return r == 0 }},
		{"最大整数", 0, 2147483647, func(r int) bool { return r == 2147483647 }},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := Add(tt.a, tt.b)
			if !tt.check(result) {
				t.Errorf("Add(%d, %d) = %d; unexpected result", tt.a, tt.b, result)
			}
		})
	}
}
```

### 带 Error 的函数测试

```go
package userstore

import (
	"errors"
	"testing"
)

// Test_UserStore_GetByID 测试获取用户
func Test_UserStore_GetByID(t *testing.T) {
	store := NewUserStore()

	tests := []struct {
		name      string
		id        string
		setup     func(*UserStore)
		wantErr   error
		checkFunc func(*User, error)
	}{
		{
			name: "用户存在",
			id:   "user-1",
			setup: func(s *UserStore) {
				s.users["user-1"] = &User{ID: "user-1", Name: "Alice"}
			},
			wantErr: nil,
			checkFunc: func(u *User, err error) {
				if u.Name != "Alice" {
					t.Errorf("expected Name=Alice, got %s", u.Name)
				}
			},
		},
		{
			name:      "用户不存在",
			id:        "not-exist",
			setup:     func(s *UserStore) {},
			wantErr:   ErrNotFound,
			checkFunc: func(u *User, err error) {
				if !errors.Is(err, ErrNotFound) {
					t.Errorf("expected ErrNotFound, got %v", err)
				}
			},
		},
		{
			name:      "空ID",
			id:        "",
			setup:     func(s *UserStore) {},
			wantErr:   ErrInvalidID,
			checkFunc: func(u *User, err error) {
				if !errors.Is(err, ErrInvalidID) {
					t.Errorf("expected ErrInvalidID, got %v", err)
				}
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.setup(store)
			user, err := store.GetByID(tt.id)
			if !errors.Is(err, tt.wantErr) {
				t.Errorf("GetByID() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			tt.checkFunc(user, err)
		})
	}
}
```

### 并发安全测试

```go
package counter

import (
	"sync"
	"testing"
)

// Test_Counter_Concurrent 测试计数器并发安全
// 使用 go test -race 运行以检测竞态条件
func Test_Counter_Concurrent(t *testing.T) {
	t.Run("并发递增", func(t *testing.T) {
		counter := NewCounter()
		const goroutines = 100
		const increments = 1000

		var wg sync.WaitGroup
		wg.Add(goroutines)

		for i := 0; i < goroutines; i++ {
			go func() {
				defer wg.Done()
				for j := 0; j < increments; j++ {
					counter.Increment()
				}
			}()
		}

		wg.Wait()

		expected := int64(goroutines * increments)
		if counter.Value() != expected {
			t.Errorf("counter.Value() = %d; want %d", counter.Value(), expected)
		}
	})

	t.Run("并发读写", func(t *testing.T) {
		store := NewSafeStore()
		const goroutines = 50
		const operations = 100

		var wg sync.WaitGroup
		wg.Add(goroutines * 2)

		// 写协程
		for i := 0; i < goroutines; i++ {
			go func(id int) {
				defer wg.Done()
				for j := 0; j < operations; j++ {
					store.Set(string(rune('a'+id%26)), j)
				}
			}(i)
		}

		// 读协程
		for i := 0; i < goroutines; i++ {
			go func(id int) {
				defer wg.Done()
				for j := 0; j < operations; j++ {
					store.Get(string(rune('a' + id%26)))
				}
			}(i)
		}

		wg.Wait()
		// 无 panic 或 data race 表示测试通过
	})
}
```

### 使用 Mock 的测试

```go
package userstore

import (
	"context"
	"errors"
	"testing"
	"time"
)

// MockClock 模拟时钟
type MockClock struct {
	now time.Time
}

func (m *MockClock) Now() time.Time {
	return m.now
}

func (m *MockClock) Set(t time.Time) {
	m.now = t
}

// ClockInterface 时钟接口（用于依赖注入）
type ClockInterface interface {
	Now() time.Time
}

// SessionManager 会话管理器（依赖时钟）
type SessionManager struct {
	clock ClockInterface
}

func NewSessionManager(clock ClockInterface) *SessionManager {
	return &SessionManager{clock: clock}
}

func (sm *SessionManager) IsExpired(expireAt time.Time) bool {
	return sm.clock.Now().After(expireAt)
}

// Test_SessionManager_IsExpired 测试会话过期
func Test_SessionManager_IsExpired(t *testing.T) {
	clock := &MockClock{now: time.Date(2024, 1, 1, 12, 0, 0, 0, time.UTC)}
	sm := NewSessionManager(clock)

	tests := []struct {
		name     string
		expireAt time.Time
		expected bool
	}{
		{"未过期", time.Date(2024, 1, 1, 13, 0, 0, 0, time.UTC), false},
		{"已过期", time.Date(2024, 1, 1, 11, 0, 0, 0, time.UTC), true},
		{"刚好过期", time.Date(2024, 1, 1, 12, 0, 0, 0, time.UTC), false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := sm.IsExpired(tt.expireAt)
			if result != tt.expected {
				t.Errorf("IsExpired() = %v; want %v", result, tt.expected)
			}
		})
	}
}

// Test_SessionManager_IsExpired_WithContext 测试带超时的会话
func Test_SessionManager_IsExpired_WithContext(t *testing.T) {
	store := NewSessionStore()

	t.Run("正常获取", func(t *testing.T) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Second)
		defer cancel()

		session, err := store.GetWithContext(ctx, "session-1")
		if err != nil {
			t.Errorf("unexpected error: %v", err)
		}
		_ = session
	})

	t.Run("超时", func(t *testing.T) {
		ctx, cancel := context.WithTimeout(context.Background(), time.Nanosecond)
		defer cancel()
		time.Sleep(time.Millisecond) // 确保超时

		_, err := store.GetWithContext(ctx, "session-1")
		if !errors.Is(err, context.DeadlineExceeded) {
			t.Errorf("expected DeadlineExceeded, got %v", err)
		}
	})
}
```

### Benchmark 测试

```go
package benchutil

import (
	"testing"
)

// Benchmark_Add 测试加法性能
func Benchmark_Add(b *testing.B) {
	for i := 0; i < b.N; i++ {
		Add(1, 2)
	}
}

// Benchmark_Add_Parallel 并行性能测试
func Benchmark_Add_Parallel(b *testing.B) {
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			Add(1, 2)
		}
	})
}
```

## 测试命名规范

| 格式 | 用途 |
|------|------|
| `Test_<Unit>_<Scenario>` | 正常/错误路径 |
| `Test_<Unit>_EdgeCases` | 边界情况 |
| `Test_<Unit>_Concurrent` | 并发测试 |
| `Test_<Unit>_WithContext` | 上下文测试 |
| `Benchmark_<Unit>` | 性能测试 |

## 最佳实践

### 1. Table-Driven Tests
```go
tests := []struct {
    name     string
    input    Type
    expected Type
}{
    {"case1", input1, expected1},
    {"case2", input2, expected2},
}
for _, tt := range tests {
    t.Run(tt.name, func(t *testing.T) {
        // 测试逻辑
    })
}
```

### 2. 并行测试
```go
func Test_Function_Parallel(t *testing.T) {
    t.Parallel()
    // 测试逻辑
}
```

### 3. 子测试并行
```go
for _, tt := range tests {
    tt := tt  // 捕获循环变量
    t.Run(tt.name, func(t *testing.T) {
        t.Parallel()
        // 测试逻辑
    })
}
```

### 4. 错误断言
```go
// 使用 errors.Is
if !errors.Is(err, expectedErr) {
    t.Errorf("expected %v, got %v", expectedErr, err)
}

// 使用 errors.As
var myErr *MyError
if !errors.As(err, &myErr) {
    t.Errorf("expected *MyError, got %T", err)
}
```

## 完整测试文件模板

```go
package packagename

import (
	"context"
	"errors"
	"testing"
	"time"
)

// 错误定义（如果需要）
var (
	ErrInvalidInput = errors.New("invalid input")
	ErrNotFound     = errors.New("not found")
)

// Test_<Unit>_<Scenario> 测试正常路径
func Test_<Unit>_<Scenario>(t *testing.T) {
	tests := []struct {
		name     string
		input    string
		expected string
	}{
		{"基本用例", "hello", "hello"},
		{"空字符串", "", ""},
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			result := FunctionUnderTest(tt.input)
			if result != tt.expected {
				t.Errorf("FunctionUnderTest(%q) = %q; want %q", tt.input, result, tt.expected)
			}
		})
	}
}

// Test_<Unit>_Errors 测试错误路径
func Test_<Unit>_Errors(t *testing.T) {
	tests := []struct {
		name      string
		input     string
		wantErr   error
		errCheck  func(error) bool
	}{
		{
			name:    "无效输入",
			input:   "invalid",
			wantErr: ErrInvalidInput,
			errCheck: func(err error) bool {
				return errors.Is(err, ErrInvalidInput)
			},
		},
	}

	for _, tt := range tests {
		tt := tt
		t.Run(tt.name, func(t *testing.T) {
			t.Parallel()
			_, err := FunctionUnderTest(tt.input)
			if !tt.errCheck(err) {
				t.Errorf("expected error %v, got %v", tt.wantErr, err)
			}
		})
	}
}

// Test_<Unit>_Concurrent 并发安全测试
func Test_<Unit>_Concurrent(t *testing.T) {
	t.Run("并发读写", func(t *testing.T) {
		obj := NewObject()
		const goroutines = 100

		done := make(chan struct{})
		var wg sync.WaitGroup
		wg.Add(goroutines * 2)

		// 写
		for i := 0; i < goroutines; i++ {
			go func(id int) {
				defer wg.Done()
				for {
					select {
					case <-done:
						return
					default:
						obj.Set(id)
					}
				}
			}(i)
		}

		// 读
		for i := 0; i < goroutines; i++ {
			go func() {
				defer wg.Done()
				for {
					select {
					case <-done:
						return
					default:
						obj.Get()
					}
				}
			}()
		}

		time.Sleep(100 * time.Millisecond)
		close(done)
		wg.Wait()
	})
}
```
