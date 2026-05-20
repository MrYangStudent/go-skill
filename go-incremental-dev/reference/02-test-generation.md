# 测试生成规范

## 测试覆盖要求

1. **正常路径测试** - 基本功能验证、多种输入组合、预期输出准确性
2. **边界情况测试** - nil 值、零值、空结构体、极端值
3. **错误路径测试** - 无效输入、错误条件、错误传播验证
4. **并发安全测试** - race condition 检测、并发读写场景

---

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
			name:    "用户不存在",
			id:      "not-exist",
			setup:   func(s *UserStore) {},
			wantErr: ErrNotFound,
			checkFunc: func(u *User, err error) {
				if !errors.Is(err, ErrNotFound) {
					t.Errorf("expected ErrNotFound, got %v", err)
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
}
```

### 边界情况测试

```go
package validator

// Test_ValidateName_EdgeCases 测试边界情况
func Test_ValidateName_EdgeCases(t *testing.T) {
	tests := []struct {
		name    string
		input   string
		wantErr bool
	}{
		{"空字符串", "", true},
		{"单字符", "A", false},
		{"正常长度", "Alice", false},
		{"最大长度", strings.Repeat("a", 100), false},
		{"超过最大长度", strings.Repeat("a", 101), true},
		{"包含空格", "Alice Wang", false},
		{"包含数字", "User123", false},
		{"纯数字", "12345", true},
		{"特殊字符", "user@#$", true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := ValidateName(tt.input)
			if (err != nil) != tt.wantErr {
				t.Errorf("ValidateName(%q) error = %v, wantErr %v", tt.input, err, tt.wantErr)
			}
		})
	}
}
```

---

## 测试命名规范

| 格式 | 用途 |
|------|------|
| `Test_<Unit>_<Scenario>` | 正常/错误路径 |
| `Test_<Unit>_EdgeCases` | 边界情况 |
| `Test_<Unit>_Concurrent` | 并发测试 |
| `Benchmark_<Unit>` | 性能测试 |

---

## Mock 编写模板

```go
package mocks

import "context"

// MockStorage 模拟存储服务
type MockStorage struct {
	data       map[string][]byte
	getErr     error
	setErr     error
	delErr     error
	onGet      func(key string)
	onSet      func(key string, value []byte)
	onDel      func(key string)
}

func NewMockStorage() *MockStorage {
	return &MockStorage{data: make(map[string][]byte)}
}

func (m *MockStorage) Get(_ context.Context, key string) ([]byte, error) {
	if m.onGet != nil {
		m.onGet(key)
	}
	if m.getErr != nil {
		return nil, m.getErr
	}
	return m.data[key], nil
}

func (m *MockStorage) Set(_ context.Context, key string, val []byte) error {
	if m.onSet != nil {
		m.onSet(key, val)
	}
	if m.setErr != nil {
		return m.setErr
	}
	m.data[key] = val
	return nil
}

func (m *MockStorage) Delete(_ context.Context, key string) error {
	if m.onDel != nil {
		m.onDel(key)
	}
	if m.delErr != nil {
		return m.delErr
	}
	delete(m.data, key)
	return nil
}
```
