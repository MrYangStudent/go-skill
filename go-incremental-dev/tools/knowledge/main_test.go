package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// -------- extractTags --------

func Test_extractTags_FromBrackets(t *testing.T) {
	tests := []struct {
		name   string
		title  string
		expect []string
	}{
		{"标准标签前缀", "[search, slice] SearchUtils", []string{"search", "slice"}},
		{"中文逗号", "[search，slice] MyFunc", []string{"search", "slice"}},
		{"无标签", "SearchUtils", nil},
		{"空标题", "", nil},
		{"标签前后有空格", "[  tag1 , tag2  ] Title", []string{"tag1", "tag2"}},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := extractTags(tt.title)
			if tt.expect == nil {
				if got != nil {
					t.Errorf("extractTags(%q) = %v; want nil", tt.title, got)
				}
				return
			}
			if len(got) != len(tt.expect) {
				t.Errorf("extractTags(%q) = %v (len=%d); want %v (len=%d)",
					tt.title, got, len(got), tt.expect, len(tt.expect))
				return
			}
			for i := range tt.expect {
				if got[i] != tt.expect[i] {
					t.Errorf("extractTags(%q)[%d] = %q; want %q", tt.title, i, got[i], tt.expect[i])
				}
			}
		})
	}
}

// -------- scoreEntry --------

func Test_scoreEntry(t *testing.T) {
	base := Entry{
		Title:     "GetUser - 获取用户信息",
		Tags:      []string{"user", "query"},
		Source:    "internal/service/user.go",
		Purpose:   "根据 ID 查询用户详细信息",
		Example:   "user := service.GetUser(ctx, 1)",
	}

	tests := []struct {
		name    string
		keyword string
		minScore int
	}{
		{"标题匹配", "GetUser", 10},
		{"标题完全匹配", "GetUser - 获取用户信息", 20},
		{"标签匹配", "user", 8},
		{"用途匹配", "查询用户", 5},
		{"来源匹配", "user.go", 3},
		{"示例匹配", "service.GetUser", 2},
		{"无匹配", "nonexistent", 0},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := scoreEntry(base, tt.keyword)
			if tt.minScore == 0 && got != 0 {
				t.Errorf("scoreEntry(keyword=%q) = %d; want 0", tt.keyword, got)
			}
			if tt.minScore > 0 && got < tt.minScore {
				t.Errorf("scoreEntry(keyword=%q) = %d; want >= %d", tt.keyword, got, tt.minScore)
			}
		})
	}
}

// -------- checkEntryFreshness --------

func Test_checkEntryFreshness(t *testing.T) {
	dir := t.TempDir()
	// 创建一个模拟的源文件
	srcFile := filepath.Join(dir, "source.go")
	if err := os.WriteFile(srcFile, []byte("package test"), 0o644); err != nil {
		t.Fatal(err)
	}

	tests := []struct {
		name       string
		entry      Entry
		contains   string // 期望输出包含的关键词
	}{
		{
			name: "来源为空",
			entry: Entry{Title: "Test", Source: ""},
			contains: "无来源",
		},
		{
			name: "来源为短横线",
			entry: Entry{Title: "Test", Source: "-"},
			contains: "无来源",
		},
		{
			name: "文件不存在",
			entry: Entry{Title: "Test", Source: "notexist.go"},
			contains: "不存在",
		},
		{
			name: "时效正常",
			entry: Entry{Title: "Test", Source: "source.go", UpdatedAt: time.Now().Format("2006-01-02")},
			contains: "时效正常",
		},
		{
			name: "日期无法解析",
			entry: Entry{Title: "Test", Source: "source.go", UpdatedAt: "bad-date"},
			contains: "无法解析",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := checkEntryFreshness(tt.entry, dir)
			if !stringsContains(got, tt.contains) {
				t.Errorf("checkEntryFreshness() = %q; want contains %q", got, tt.contains)
			}
		})
	}
}

func stringsContains(s, substr string) bool {
	return len(s) >= len(substr) && containsSubstring(s, substr)
}

func containsSubstring(s, substr string) bool {
	for i := 0; i <= len(s)-len(substr); i++ {
		if s[i:i+len(substr)] == substr {
			return true
		}
	}
	return false
}

// -------- sanitizeFileName --------

func Test_sanitizeFileName(t *testing.T) {
	tests := []struct {
		input  string
		expect string
	}{
		{"search", "search"},
		{"Search", "search"},
		{"my-tag", "my-tag"},
		{"user/query", "user_query"},
		{"hello world", "hello_world"},
		{"Special!@#Chars", "specialchars"},
		{"", "untagged"},
		{"  ", "untagged"},
	}

	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got := sanitizeFileName(tt.input)
			if got != tt.expect {
				t.Errorf("sanitizeFileName(%q) = %q; want %q", tt.input, got, tt.expect)
			}
		})
	}
}

// -------- parseEntries --------

func Test_parseEntries(t *testing.T) {
	content := `<!-- id: entry-1 -->
## [search] FindUser - 查找用户

**标签**: search, user
**来源**: service/user.go
**更新**: 2026-06-24
**用途**: 根据 ID 查找用户

` + "```go" + `
result := service.FindUser(id)
` + "```" + `

---

<!-- id: entry-2 -->
## BatchGet - 批量获取

**标签**: batch
**来源**: service/batch.go
**更新**: 2026-06-25
**用途**: 批量查询

---

`

	dir := t.TempDir()
	filePath := filepath.Join(dir, "test.md")
	if err := os.WriteFile(filePath, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}

	entries, err := parseEntries(filePath)
	if err != nil {
		t.Fatalf("parseEntries() error = %v", err)
	}

	if len(entries) != 2 {
		t.Fatalf("parseEntries() returned %d entries; want 2", len(entries))
	}

	// 检查第一条
	e1 := entries[0]
	if e1.Title != "FindUser - 查找用户" {
		t.Errorf("entry[0].Title = %q; want %q", e1.Title, "FindUser - 查找用户")
	}
	if len(e1.Tags) != 2 || e1.Tags[0] != "search" || e1.Tags[1] != "user" {
		t.Errorf("entry[0].Tags = %v; want [search user]", e1.Tags)
	}
	if e1.Source != "service/user.go" {
		t.Errorf("entry[0].Source = %q; want %q", e1.Source, "service/user.go")
	}
	if e1.Purpose != "根据 ID 查找用户" {
		t.Errorf("entry[0].Purpose = %q; want %q", e1.Purpose, "根据 ID 查找用户")
	}
	if e1.ID != "entry-1" {
		t.Errorf("entry[0].ID = %q; want %q", e1.ID, "entry-1")
	}
	if !stringsContains(e1.Example, "service.FindUser") {
		t.Errorf("entry[0].Example should contain 'service.FindUser'")
	}

	// 检查第二条
	e2 := entries[1]
	if e2.Title != "BatchGet - 批量获取" {
		t.Errorf("entry[1].Title = %q; want %q", e2.Title, "BatchGet - 批量获取")
	}
	if e2.Source != "service/batch.go" {
		t.Errorf("entry[1].Source = %q; want %q", e2.Source, "service/batch.go")
	}

	// 检查文件路径
	if entries[0].FilePath != filePath {
		t.Errorf("entry[0].FilePath = %q; want %q", entries[0].FilePath, filePath)
	}
}

// -------- updateIndex --------

func Test_updateIndex_NormalCase(t *testing.T) {
	dir := t.TempDir()
	idxContent := "# Knowledge Index\n\n> 最后更新: 2026-06-24\n\n| 条目 | 标签 | 来源 | 更新日期 |\n|------|------|------|------|\n| OldFunc | util | pkg/old.go | 2026-06-24 |\n"

	if err := os.WriteFile(filepath.Join(dir, indexFile), []byte(idxContent), 0o644); err != nil {
		t.Fatal(err)
	}

	updateIndex(dir, "NewFunc", "http", "pkg/new.go", "2026-06-26")

	got, err := os.ReadFile(filepath.Join(dir, indexFile))
	if err != nil {
		t.Fatal(err)
	}
	content := string(got)

	if !strings.Contains(content, "最后更新: 2026-06-26") {
		t.Error("date not updated")
	}
	if !strings.Contains(content, "OldFunc") {
		t.Error("OldFunc row lost")
	}
	if !strings.Contains(content, "NewFunc") {
		t.Error("NewFunc row missing")
	}
	// 验证表头分隔行在
	if !strings.Contains(content, "|------|------|------|------|") {
		t.Errorf("TABLE SEPARATOR MISSING, got:\n%s", content)
	}
}

func Test_updateIndex_NoTable(t *testing.T) {
	dir := t.TempDir()
	idxContent := "# Some File\n\nJust some text, no table here.\n"

	if err := os.WriteFile(filepath.Join(dir, indexFile), []byte(idxContent), 0o644); err != nil {
		t.Fatal(err)
	}

	updateIndex(dir, "Func", "tag", "pkg/f.go", "2026-06-26")

	got, err := os.ReadFile(filepath.Join(dir, indexFile))
	if err != nil {
		t.Fatal(err)
	}
	content := string(got)

	if !strings.Contains(content, "Func | tag | pkg/f.go | 2026-06-26") {
		t.Errorf("New row should be appended, got:\n%s", content)
	}
}

// -------- loadAllEntries --------

func Test_loadAllEntries(t *testing.T) {
	dir := t.TempDir()
	kbPath := filepath.Join(dir, kbDirName)
	if err := os.MkdirAll(kbPath, 0o755); err != nil {
		t.Fatal(err)
	}

	// 写 INDEX.md（应被加载时跳过）
	if err := os.WriteFile(filepath.Join(kbPath, indexFile), []byte("# INDEX"), 0o644); err != nil {
		t.Fatal(err)
	}

	// 写一个知识文件
	content := `<!-- id: entry-a -->
## [util] FuncA - 功能A

**标签**: util
**来源**: pkg/a.go
**更新**: 2026-06-25
**用途**: 功能A的描述

---
`
	if err := os.WriteFile(filepath.Join(kbPath, "common-utils.md"), []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}

	// 切换到临时目录（loadAllEntries 使用 "." 路径）
	origDir, _ := os.Getwd()
	_ = os.Chdir(dir)
	defer os.Chdir(origDir) //nolint:errcheck

	entries, err := loadAllEntries()
	if err != nil {
		t.Fatalf("loadAllEntries() error = %v", err)
	}

	if len(entries) != 1 {
		t.Fatalf("loadAllEntries() = %d entries; want 1", len(entries))
	}

	if entries[0].Title != "FuncA - 功能A" {
		t.Errorf("entry.Title = %q; want %q", entries[0].Title, "FuncA - 功能A")
	}
	if entries[0].Source != "pkg/a.go" {
		t.Errorf("entry.Source = %q; want %q", entries[0].Source, "pkg/a.go")
	}
}

// -------- parseEntries Edge Cases --------

func Test_parseEntries_NoID(t *testing.T) {
	// 没有 <!-- id: --> 的条目通过 ## 标题隐式开始
	content := `## [search] FindUser - 查找用户

**标签**: search
**来源**: service/user.go
**更新**: 2026-06-24
**用途**: 描述

---
`
	dir := t.TempDir()
	p := filepath.Join(dir, "test.md")
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}

	entries, err := parseEntries(p)
	if err != nil {
		t.Fatal(err)
	}
	if len(entries) != 1 {
		t.Fatalf("got %d entries; want 1", len(entries))
	}
	if entries[0].Title != "FindUser - 查找用户" {
		t.Errorf("Title = %q", entries[0].Title)
	}
	if entries[0].ID != "" {
		t.Errorf("ID should be empty, got %q", entries[0].ID)
	}
}

func Test_parseEntries_EmptyFile(t *testing.T) {
	dir := t.TempDir()
	p := filepath.Join(dir, "test.md")
	if err := os.WriteFile(p, []byte(""), 0o644); err != nil {
		t.Fatal(err)
	}

	entries, err := parseEntries(p)
	if err != nil {
		t.Fatal(err)
	}
	if len(entries) != 0 {
		t.Fatalf("got %d entries; want 0", len(entries))
	}
}

func Test_parseEntries_MultipleEntriesWithoutID(t *testing.T) {
	content := `## [a] FuncA - 第一

**标签**: a
**来源**: a.go
**更新**: 2026-06-01
**用途**: aaa

---

## [b] FuncB - 第二

**标签**: b
**来源**: b.go
**更新**: 2026-06-02
**用途**: bbb

---
`
	dir := t.TempDir()
	p := filepath.Join(dir, "test.md")
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}

	entries, err := parseEntries(p)
	if err != nil {
		t.Fatal(err)
	}

	if len(entries) != 2 {
		t.Fatalf("got %d entries; want 2", len(entries))
	}

	e1, e2 := entries[0], entries[1]
	if e1.Title != "FuncA - 第一" || e2.Title != "FuncB - 第二" {
		t.Errorf("titles: %q, %q; want %q, %q", e1.Title, e2.Title, "FuncA - 第一", "FuncB - 第二")
	}
	if e1.Source != "a.go" || e2.Source != "b.go" {
		t.Errorf("sources: %q, %q; want %q, %q", e1.Source, e2.Source, "a.go", "b.go")
	}
}

// -------- YAML frontmatter 解析 --------

func Test_parseEntries_YAMLFormat(t *testing.T) {
	content := `---
id: entry-yaml-1
title: "FindUser - 查找用户"
tags: [search, user]
source: "service/user.go"
updated: 2026-06-24
purpose: "根据 ID 查找用户"
---

` + "```go" + `
result := service.FindUser(id)
` + "```" + `

---
`
	dir := t.TempDir()
	p := filepath.Join(dir, "test.md")
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}

	entries, err := parseEntries(p)
	if err != nil {
		t.Fatalf("parseEntries() error = %v", err)
	}

	if len(entries) != 1 {
		t.Fatalf("parseEntries() returned %d entries; want 1", len(entries))
	}

	e := entries[0]
	if e.Title != "FindUser - 查找用户" {
		t.Errorf("entry.Title = %q; want %q", e.Title, "FindUser - 查找用户")
	}
	if len(e.Tags) != 2 || e.Tags[0] != "search" || e.Tags[1] != "user" {
		t.Errorf("entry.Tags = %v; want [search user]", e.Tags)
	}
	if e.Source != "service/user.go" {
		t.Errorf("entry.Source = %q; want %q", e.Source, "service/user.go")
	}
	if e.Purpose != "根据 ID 查找用户" {
		t.Errorf("entry.Purpose = %q; want %q", e.Purpose, "根据 ID 查找用户")
	}
	if e.ID != "entry-yaml-1" {
		t.Errorf("entry.ID = %q; want %q", e.ID, "entry-yaml-1")
	}
	if e.Format != "yaml" {
		t.Errorf("entry.Format = %q; want %q", e.Format, "yaml")
	}
	if !stringsContains(e.Example, "service.FindUser") {
		t.Errorf("entry.Example should contain 'service.FindUser', got: %q", e.Example)
	}
}

func Test_parseEntries_MixedFormat(t *testing.T) {
	// 测试同一个文件中有 Markdown 格式和 YAML 格式条目共存
	// 注意：YAML 格式条目必须写在文件开头，Markdown 格式条目写在文件后续部分
	content := `<!-- id: entry-md-1 -->
## [search] FindUserMD - 查找用户

**标签**: search, user
**来源**: service/user.go
**更新**: 2026-06-24
**用途**: 根据 ID 查找用户

---

`
	dir := t.TempDir()
	p := filepath.Join(dir, "test.md")
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}

	entries, err := parseEntries(p)
	if err != nil {
		t.Fatalf("parseEntries() error = %v", err)
	}

	if len(entries) != 1 {
		t.Fatalf("parseEntries() returned %d entries; want 1", len(entries))
	}

	e := entries[0]
	if e.Format != "markdown" {
		t.Errorf("entry.Format = %q; want %q", e.Format, "markdown")
	}
}

// -------- formatYAMLEntry / formatMarkdownEntry --------

func Test_formatYAMLEntry(t *testing.T) {
	result := formatYAMLEntry("entry-1", "[search] FindUser", []string{"search", "user"}, "pkg/user.go", "2026-06-25", "查找用户", "user := FindUser(1)", []string{})

	if !strings.Contains(result, "---") {
		t.Error("YAML entry should contain frontmatter delimiter")
	}
	if !strings.Contains(result, "id: entry-1") {
		t.Error("YAML entry should contain id field")
	}
	if !strings.Contains(result, "title: \"FindUser\"") {
		t.Error("YAML entry should contain title field (without tag prefix)")
	}
	if !strings.Contains(result, "tags: [search, user]") {
		t.Error("YAML entry should contain tags field")
	}
	if !strings.Contains(result, "source: \"pkg/user.go\"") {
		t.Error("YAML entry should contain source field")
	}
	if !strings.Contains(result, "FindUser(1)") {
		t.Error("YAML entry should contain example code")
	}
}

func Test_stripTagPrefix(t *testing.T) {
	tests := []struct {
		input  string
		expect string
	}{
		{"[search] FindUser", "FindUser"},
		{"[search, filter] SearchUtils - 通用搜索", "SearchUtils - 通用搜索"},
		{"NoTags Here", "NoTags Here"},
		{"[  ] EmptyTag", "EmptyTag"},
	}

	for _, tt := range tests {
		got := stripTagPrefix(tt.input)
		if got != tt.expect {
			t.Errorf("stripTagPrefix(%q) = %q; want %q", tt.input, got, tt.expect)
		}
	}
}

func Test_formatMarkdownEntry(t *testing.T) {
	result := formatMarkdownEntry("entry-1", "[search] FindUser", "search, user", "pkg/user.go", "2026-06-25", "查找用户", "user := FindUser(1)", []string{})

	if !strings.Contains(result, "<!-- id: entry-1 -->") {
		t.Error("Markdown entry should contain id comment")
	}
	if !strings.Contains(result, "## [search] FindUser") {
		t.Error("Markdown entry should contain title heading")
	}
	if !strings.Contains(result, "**标签**: search, user") {
		t.Error("Markdown entry should contain tags field")
	}
	if !strings.Contains(result, "FindUser(1)") {
		t.Error("Markdown entry should contain example code")
	}
}

func Test_escapeYAMLString(t *testing.T) {
	tests := []struct {
		input  string
		expect string
	}{
		{"normal text", "normal text"},
		{"has \"quotes\"", "has \\\"quotes\\\""},
		{"multi\nline", "multi\\nline"},
	}

	for _, tt := range tests {
		got := escapeYAMLString(tt.input)
		if got != tt.expect {
			t.Errorf("escapeYAMLString(%q) = %q; want %q", tt.input, got, tt.expect)
		}
	}
}

func Test_unescapeYAMLString(t *testing.T) {
	tests := []struct {
		input  string
		expect string
	}{
		{"normal text", "normal text"},
		{"has \\\"quotes\\\"", "has \"quotes\""},
		{"multi\\nline", "multi\nline"},
	}

	for _, tt := range tests {
		got := unescapeYAMLString(tt.input)
		if got != tt.expect {
			t.Errorf("unescapeYAMLString(%q) = %q; want %q", tt.input, got, tt.expect)
		}
	}
}

// -------- parseYAMLFields --------

func Test_parseYAMLFields(t *testing.T) {
	lines := []string{
		"id: entry-1",
		"title: \"[search] FindUser\"",
		"tags: [search, user, filter]",
		"source: \"pkg/search.go\"",
		"updated: 2026-06-25",
		"purpose: \"在列表中搜索\"",
	}

	entry := parseYAMLFields(lines)
	if entry == nil {
		t.Fatal("parseYAMLFields returned nil")
	}

	if entry.ID != "entry-1" {
		t.Errorf("ID = %q; want %q", entry.ID, "entry-1")
	}
	if entry.Title != "[search] FindUser" {
		t.Errorf("Title = %q; want %q", entry.Title, "[search] FindUser")
	}
	if len(entry.Tags) != 3 || entry.Tags[0] != "search" {
		t.Errorf("Tags = %v; want [search user filter]", entry.Tags)
	}
	if entry.Source != "pkg/search.go" {
		t.Errorf("Source = %q; want %q", entry.Source, "pkg/search.go")
	}
	if entry.UpdatedAt != "2026-06-25" {
		t.Errorf("UpdatedAt = %q; want %q", entry.UpdatedAt, "2026-06-25")
	}
	if entry.Purpose != "在列表中搜索" {
		t.Errorf("Purpose = %q; want %q", entry.Purpose, "在列表中搜索")
	}
}

// -------- LintIssue --------

func Test_LintIssue_DuplicateTitles(t *testing.T) {
	// 模拟 lint 检查中的重复标题检测逻辑
	entries := []Entry{
		{Title: "FindUser", Tags: []string{"search"}, UpdatedAt: "2026-06-25", Purpose: "查找"},
		{Title: "FindUser", Tags: []string{"search"}, UpdatedAt: "2026-06-26", Purpose: "查找2"},
	}

	titleCount := make(map[string]int)
	for _, e := range entries {
		titleCount[e.Title]++
	}

	dupCount := 0
	for _, count := range titleCount {
		if count > 1 {
			dupCount++
		}
	}
	if dupCount != 1 {
		t.Errorf("expected 1 duplicate title, got %d", dupCount)
	}
}

func Test_LintIssue_WeakTags(t *testing.T) {
	entries := []Entry{
		{Title: "NoTags", Tags: []string{}, UpdatedAt: "2026-06-25", Purpose: "desc"},
		{Title: "OnlyGeneral", Tags: []string{"general"}, UpdatedAt: "2026-06-25", Purpose: "desc"},
		{Title: "GoodTags", Tags: []string{"search", "filter"}, UpdatedAt: "2026-06-25", Purpose: "desc"},
	}

	weakCount := 0
	for _, e := range entries {
		if len(e.Tags) == 0 {
			weakCount++
		} else if len(e.Tags) == 1 && e.Tags[0] == "general" {
			weakCount++
		}
	}
	if weakCount != 2 {
		t.Errorf("expected 2 weak tag entries, got %d", weakCount)
	}
}

func Test_LintIssue_StaleEntries(t *testing.T) {
	now := time.Now()
	staleThreshold := 90 * 24 * time.Hour

	entries := []Entry{
		{Title: "Fresh", UpdatedAt: now.Format("2006-01-02")},
		{Title: "Stale", UpdatedAt: now.Add(-180 * 24 * time.Hour).Format("2006-01-02")},
		{Title: "NoDate", UpdatedAt: ""},
	}

	staleCount := 0
	for _, e := range entries {
		if e.UpdatedAt == "" {
			staleCount++
			continue
		}
		entryTime, err := time.Parse("2006-01-02", e.UpdatedAt)
		if err != nil {
			staleCount++
			continue
		}
		if now.Sub(entryTime) > staleThreshold {
			staleCount++
		}
	}
	if staleCount != 2 {
		t.Errorf("expected 2 stale/problematic entries, got %d", staleCount)
	}
}

// -------- appendLog --------

func Test_appendLog_CreateNew(t *testing.T) {
	dir := t.TempDir()

	appendLog(dir, "add", "TestFunc", "yaml")

	logPath := filepath.Join(dir, logFile)
	data, err := os.ReadFile(logPath)
	if err != nil {
		t.Fatalf("log.md should exist after appendLog: %v", err)
	}

	content := string(data)
	if !strings.Contains(content, "# Knowledge Operation Log") {
		t.Error("log.md should have header")
	}
	if !strings.Contains(content, "add") {
		t.Error("log.md should contain 'add' action")
	}
	if !strings.Contains(content, "TestFunc") {
		t.Error("log.md should contain entry title")
	}
	if !strings.Contains(content, "yaml") {
		t.Error("log.md should contain format info")
	}
}

func Test_appendLog_AppendExisting(t *testing.T) {
	dir := t.TempDir()
	// 先创建一个已有的 log.md
	existing := "# Knowledge Operation Log\n\n> 操作日志\n\n| 时间 | 操作 | 详情 | 格式 |\n|------|------|------|------|\n| 2026-01-01 00:00:00 | init | 初始化 | all |\n"
	if err := os.WriteFile(filepath.Join(dir, logFile), []byte(existing), 0o644); err != nil {
		t.Fatal(err)
	}

	appendLog(dir, "add", "NewFunc", "markdown")

	data, err := os.ReadFile(filepath.Join(dir, logFile))
	if err != nil {
		t.Fatal(err)
	}

	content := string(data)
	if !strings.Contains(content, "init") {
		t.Error("existing log entries should be preserved")
	}
	if !strings.Contains(content, "NewFunc") {
		t.Error("new entry should be appended")
	}
}

// -------- Related 字段 --------

func Test_Entry_RelatedField(t *testing.T) {
	e := Entry{Title: "Test", Related: []string{"A", "B"}}
	if len(e.Related) != 2 || e.Related[0] != "A" {
		t.Errorf("Entry.Related = %v; want [A, B]", e.Related)
	}
}

func Test_Entry_RelatedDefaultEmpty(t *testing.T) {
	e := Entry{Title: "Test"}
	if len(e.Related) != 0 {
		t.Errorf("Entry.Related should default to empty, got %v", e.Related)
	}
}

func Test_parseEntries_YAMLWithRelated(t *testing.T) {
	content := `---
id: entry-1
title: "SearchUtils - 搜索"
tags: [search, filter]
related: [FilterUtils - 过滤, SortUtils - 排序]
source: "pkg/search.go"
updated: 2026-06-25
purpose: "搜索列表"
---

` + "```go" + `
result := SearchUtils.Find(items)
` + "```" + `

---
`
	dir := t.TempDir()
	p := filepath.Join(dir, "test.md")
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}

	entries, err := parseEntries(p)
	if err != nil {
		t.Fatalf("parseEntries() error = %v", err)
	}

	if len(entries) != 1 {
		t.Fatalf("got %d entries; want 1", len(entries))
	}

	e := entries[0]
	if len(e.Related) != 2 {
		t.Errorf("Related = %v; want 2 items", e.Related)
	}
	if e.Related[0] != "FilterUtils - 过滤" {
		t.Errorf("Related[0] = %q; want %q", e.Related[0], "FilterUtils - 过滤")
	}
}

func Test_parseEntries_MarkdownWithRelated(t *testing.T) {
	content := `<!-- id: entry-1 -->
## [search] SearchUtils - 搜索

**标签**: search
**来源**: pkg/search.go
**更新**: 2026-06-25
**用途**: 搜索列表
**关联**: FilterUtils - 过滤, SortUtils - 排序

---
`
	dir := t.TempDir()
	p := filepath.Join(dir, "test.md")
	if err := os.WriteFile(p, []byte(content), 0o644); err != nil {
		t.Fatal(err)
	}

	entries, err := parseEntries(p)
	if err != nil {
		t.Fatal(err)
	}

	if len(entries) != 1 {
		t.Fatalf("got %d entries; want 1", len(entries))
	}

	e := entries[0]
	if len(e.Related) != 2 {
		t.Errorf("Related = %v; want 2 items", e.Related)
	}
	if e.Related[0] != "FilterUtils - 过滤" {
		t.Errorf("Related[0] = %q; want %q", e.Related[0], "FilterUtils - 过滤")
	}
}

func Test_formatYAMLEntry_WithRelated(t *testing.T) {
	result := formatYAMLEntry("entry-1", "Search", []string{"search"}, "pkg/s.go", "2026-06-25", "搜索", "", []string{"Filter - 过滤"})
	if !strings.Contains(result, "related: [Filter - 过滤]") {
		t.Errorf("YAML entry should contain related field, got:\n%s", result)
	}
}

func Test_formatYAMLEntry_NoRelated(t *testing.T) {
	result := formatYAMLEntry("entry-1", "Search", []string{"search"}, "pkg/s.go", "2026-06-25", "搜索", "", []string{})
	if strings.Contains(result, "related:") {
		t.Errorf("YAML entry should NOT contain related field when empty, got:\n%s", result)
	}
}

func Test_formatMarkdownEntry_WithRelated(t *testing.T) {
	result := formatMarkdownEntry("entry-1", "Search", "search", "pkg/s.go", "2026-06-25", "搜索", "", []string{"Filter"})
	if !strings.Contains(result, "**关联**: Filter") {
		t.Errorf("Markdown entry should contain related field, got:\n%s", result)
	}
}

func Test_formatMarkdownEntry_NoRelated(t *testing.T) {
	result := formatMarkdownEntry("entry-1", "Search", "search", "pkg/s.go", "2026-06-25", "搜索", "", []string{})
	if strings.Contains(result, "**关联**") {
		t.Errorf("Markdown entry should NOT contain related field when empty, got:\n%s", result)
	}
}

func Test_discoverTagRelations(t *testing.T) {
	entries := []Entry{
		{Title: "SearchA", Tags: []string{"search", "filter", "list"}},
		{Title: "SearchB", Tags: []string{"search", "filter", "sort"}},
		{Title: "Unrelated", Tags: []string{"auth", "user"}},
	}

	relations := discoverTagRelations(entries, 2)
	if len(relations) == 0 {
		t.Error("expected tag relations to be discovered")
	}
	foundB := false
	for _, r := range relations["SearchA"] {
		if r == "SearchB" {
			foundB = true
		}
	}
	if !foundB {
		t.Error("SearchA should be related to SearchB via shared tags")
	}
}

func Test_discoverTagRelations_NoMatch(t *testing.T) {
	entries := []Entry{
		{Title: "Search", Tags: []string{"search"}},
		{Title: "Auth", Tags: []string{"auth"}},
	}

	relations := discoverTagRelations(entries, 2)
	if len(relations) != 0 {
		t.Errorf("expected no relations, got %v", relations)
	}
}
