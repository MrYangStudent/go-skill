# JSON 工具封装 (jsonx)

## 常用 JSON 操作封装

```go
package jsonx

import (
    "encoding/json"
    "fmt"
    "io"
)

// MarshalPretty 格式化 JSON 编码，带缩进。
func MarshalPretty(v any) ([]byte, error) {
    return json.MarshalIndent(v, "", "  ")
}

// UnmarshalFromString 从字符串解码 JSON。
func UnmarshalFromString(data string, v any) error {
    return json.Unmarshal([]byte(data), v)
}

// MarshalToString 编码为 JSON 字符串。
func MarshalToString(v any) (string, error) {
    data, err := json.Marshal(v)
    if err != nil {
        return "", fmt.Errorf("marshal to string: %w", err)
    }
    return string(data), nil
}

// DecodeFromReader 从 io.Reader 解码 JSON。
func DecodeFromReader(r io.Reader, v any) error {
    decoder := json.NewDecoder(r)
    if err := decoder.Decode(v); err != nil {
        return fmt.Errorf("decode from reader: %w", err)
    }
    return nil
}

// GetFromRaw 从 json.RawMessage 中提取指定字段。
// 适用于不确定完整结构，只需部分字段的场景。
func GetFromRaw(raw json.RawMessage, key string) (json.RawMessage, error) {
    var obj map[string]json.RawMessage
    if err := json.Unmarshal(raw, &obj); err != nil {
        return nil, fmt.Errorf("unmarshal raw message: %w", err)
    }
    val, ok := obj[key]
    if !ok {
        return nil, fmt.Errorf("key %q not found", key)
    }
    return val, nil
}

// MustMarshal 编码 JSON，panic on error（仅用于初始化或测试）。
func MustMarshal(v any) []byte {
    data, err := json.Marshal(v)
    if err != nil {
        panic(fmt.Sprintf("jsonx.MustMarshal: %v", err))
    }
    return data
}

// MustMarshalToString 编码为 JSON 字符串，panic on error（仅用于初始化或测试）。
func MustMarshalToString(v any) string {
    s, err := MarshalToString(v)
    if err != nil {
        panic(fmt.Sprintf("jsonx.MustMarshalToString: %v", err))
    }
    return s
}

// IsJSON 判断字符串是否为合法 JSON。
func IsJSON(s string) bool {
    var v any
    return json.Unmarshal([]byte(s), &v) == nil
}

// MergeRaw 合并两个 json.RawMessage，后者覆盖前者的同名 key。
func MergeRaw(a, b json.RawMessage) (json.RawMessage, error) {
    var mapA, mapB map[string]any
    if err := json.Unmarshal(a, &mapA); err != nil {
        return nil, fmt.Errorf("unmarshal first raw: %w", err)
    }
    if err := json.Unmarshal(b, &mapB); err != nil {
        return nil, fmt.Errorf("unmarshal second raw: %w", err)
    }
    for k, v := range mapB {
        mapA[k] = v
    }
    result, err := json.Marshal(mapA)
    if err != nil {
        return nil, fmt.Errorf("marshal merged: %w", err)
    }
    return result, nil
}
```

## 使用示例

```go
// 格式化输出
data, _ := jsonx.MarshalPretty(config)
fmt.Println(string(data))

// 快速解码字符串
var user User
if err := jsonx.UnmarshalFromString(jsonStr, &user); err != nil {
    return err
}

// 提取部分字段
rawID, err := jsonx.GetFromRaw(rawBody, "id")
if err != nil {
    return err
}

// 安全合并
merged, err := jsonx.MergeRaw(defaults, overrides)
```
