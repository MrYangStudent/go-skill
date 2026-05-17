# 字符串工具封装 (strx)

## 常用字符串操作封装

```go
package strx

import (
    "strings"
    "unicode"
)

// IsBlank 判断字符串是否为空或仅含空白字符。
func IsBlank(s string) bool {
    return len(strings.TrimSpace(s)) == 0
}

// IsNotBlank 判断字符串是否非空且含非空白字符。
func IsNotBlank(s string) bool {
    return !IsBlank(s)
}

// DefaultIfBlank 如果字符串为空则返回默认值。
func DefaultIfBlank(s, defaultVal string) string {
    if IsBlank(s) {
        return defaultVal
    }
    return s
}

// Truncate 截断字符串，超过 maxLen 时追加 suffix（如 "..."）。
// 返回的字符串总长度不超过 maxLen。
func Truncate(s string, maxLen int, suffix string) string {
    if len(s) <= maxLen {
        return s
    }
    if maxLen <= len(suffix) {
        return s[:maxLen]
    }
    return s[:maxLen-len(suffix)] + suffix
}

// TrimAll 去除字符串中所有空白字符（不仅是首尾）。
func TrimAll(s string) string {
    var b strings.Builder
    b.Grow(len(s))
    for _, r := range s {
        if !unicode.IsSpace(r) {
            b.WriteRune(r)
        }
    }
    return b.String()
}

// Capitalize 首字母大写。
func Capitalize(s string) string {
    if len(s) == 0 {
        return s
    }
    runes := []rune(s)
    runes[0] = unicode.ToUpper(runes[0])
    return string(runes)
}

// CamelToSnake 驼峰转蛇形命名。如 "UserName" -> "user_name"。
func CamelToSnake(s string) string {
    var b strings.Builder
    for i, r := range s {
        if unicode.IsUpper(r) {
            if i > 0 {
                b.WriteByte('_')
            }
            b.WriteRune(unicode.ToLower(r))
        } else {
            b.WriteRune(r)
        }
    }
    return b.String()
}

// SnakeToCamel 蛇形转驼峰命名。如 "user_name" -> "UserName"。
func SnakeToCamel(s string) string {
    parts := strings.Split(s, "_")
    for i := range parts {
        if len(parts[i]) > 0 {
            parts[i] = strings.ToUpper(parts[i][:1]) + parts[i][1:]
        }
    }
    return strings.Join(parts, "")
}

// SnakeToLowerCamel 蛇形转小驼峰命名。如 "user_name" -> "userName"。
func SnakeToLowerCamel(s string) string {
    parts := strings.Split(s, "_")
    for i := 1; i < len(parts); i++ {
        if len(parts[i]) > 0 {
            parts[i] = strings.ToUpper(parts[i][:1]) + parts[i][1:]
        }
    }
    return strings.Join(parts, "")
}

// Substring 安全的子字符串截取，不会 panic。
// start 和 end 为字符（rune）索引，支持负数表示从末尾计数。
func Substring(s string, start, end int) string {
    runes := []rune(s)
    length := len(runes)

    if start < 0 {
        start = length + start
    }
    if end < 0 {
        end = length + end
    }

    if start < 0 {
        start = 0
    }
    if end > length {
        end = length
    }
    if start >= end {
        return ""
    }

    return string(runes[start:end])
}

// Reverse 反转字符串（支持 Unicode）。
func Reverse(s string) string {
    runes := []rune(s)
    for i, j := 0, len(runes)-1; i < j; i, j = i+1, j-1 {
        runes[i], runes[j] = runes[j], runes[i]
    }
    return string(runes)
}

// PadLeft 左填充到指定长度。
func PadLeft(s string, padChar rune, length int) string {
    if len(s) >= length {
        return s
    }
    padding := strings.Repeat(string(padChar), length-len(s))
    return padding + s
}

// PadRight 右填充到指定长度。
func PadRight(s string, padChar rune, length int) string {
    if len(s) >= length {
        return s
    }
    padding := strings.Repeat(string(padChar), length-len(s))
    return s + padding
}
```

## 使用示例

```go
// 空值检查
if strx.IsBlank(userInput) {
    return errors.New("input cannot be empty")
}

// 截断长文本
summary := strx.Truncate(longText, 100, "...")

// 命名转换
tableName := strx.CamelToSnake("UserName") // "user_name"
jsonKey := strx.SnakeToLowerCamel("user_name") // "userName"

// 安全截取
sub := strx.Substring("你好世界", 0, 2) // "你好"

// 填充
id := strx.PadLeft("42", '0', 6) // "000042"
```
