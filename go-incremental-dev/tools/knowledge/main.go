// Knowledge 知识库管理工具
//
// 用于增量开发场景下沉淀、检索和更新项目可复用知识。
// 零外部依赖，纯 Go 标准库实现。
//
// 用法:
//
//	go run main.go init                    # 初始化知识库
//	go run main.go add                     # 交互式新增条目
//	go run main.go add -t "标题" -c "内容" -s "来源文件"  # 命令行新增
//	go run main.go search <关键词>          # 搜索知识条目
//	go run main.go list                    # 列出所有条目
//	go run main.go list --stale <目录>      # 标记过时条目
//	go run main.go check-stale <项目目录>   # 检查条目是否过期
package main

import (
	"bufio"
	"flag"
	"fmt"
	"go/ast"
	"go/parser"
	"go/token"
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

const (
	kbDirName    = "project-knowledge"
	indexFile    = "INDEX.md"
	logFile      = "log.md"
)

// Entry 表示一条知识条目.
type Entry struct {
	ID        string
	Title     string
	Tags      []string
	Source    string
	UpdatedAt string
	Purpose   string
	Example   string
	FilePath  string
	LineNum   int
	Format    string // "markdown" 或 "yaml"，标记条目格式类型
	Related   []string // 关联条目 title 列表
}

var (
	// 元数据正则：<!-- key: value -->
	metaRe = regexp.MustCompile(`<!--\s*(\w[\w-]*)\s*:\s*(.*?)\s*-->`)
	// 标题正则：## [tag] Title
	titleRe = regexp.MustCompile(`^##\s+(\[[^\]]+\]\s*)?(.+)$`)
	// 字段正则：**字段名**: 值
	fieldRe = regexp.MustCompile(`^\*\*([^*]+)\*\*\s*:\s*(.+)$`)
	// YAML frontmatter 开始/结束标记
	yamlDelimRe = regexp.MustCompile(`^---\s*$`)
	// YAML 字段正则：key: value 或 key: [a, b]
	yamlFieldRe = regexp.MustCompile(`^(\w+)\s*:\s*(.+)$`)
	// YAML 数组正则：[item1, item2]
	yamlArrayRe = regexp.MustCompile(`^\[([^\]]+)\]$`)
)

func main() {
	if len(os.Args) < 2 {
		printUsage()
		os.Exit(1)
	}

	cmd := os.Args[1]
	args := os.Args[2:]

	switch cmd {
	case "init":
		runInit(args)
	case "add":
		runAdd(args)
	case "search":
		runSearch(args)
	case "list":
		runList(args)
	case "check-stale":
		runCheckStale(args)
	case "reindex":
		runReindex()
	case "scan":
		runScan(args)
	case "lint":
		runLint(args)
	case "link":
		runLink(args)
	case "help", "--help", "-h":
		printUsage()
	default:
		fmt.Fprintf(os.Stderr, "未知命令: %s\n\n", cmd)
		printUsage()
		os.Exit(1)
	}
}

// printUsage 输出命令帮助信息.
func printUsage() {
	fmt.Print(`Knowledge — 知识库管理工具

用法:
  knowledge init                   初始化知识库目录结构
  knowledge add                   交互式添加知识条目
  knowledge add -t "标题" -s "来源" -p "用途" [-e "示例代码"] [--format yaml|markdown]  命令行添加
  knowledge search <关键词>        搜索知识条目
  knowledge list                  列出所有条目
  knowledge list --stale <项目目录> 列出过时条目
  knowledge check-stale <项目目录>  检查并报告过期条目
  knowledge reindex                 从内容文件重建 INDEX.md
  knowledge scan [目录...]           扫描项目代码提取可导出函数
  knowledge lint                   知识库完整性检查（重复标题、弱标签、过旧条目、索引不一致）
  knowledge link [项目目录]           自动发现条目间的关联关系（import分析 + 标签相似度）

格式选项:
  --format yaml       使用 YAML frontmatter 格式（推荐新条目使用）
  --format markdown   使用 Markdown 字段格式（默认，兼容旧项目）
`)
}

// ---------- init ----------

// runInit 初始化 project-knowledge/ 目录并创建 INDEX.md.
func runInit(args []string) {
	dir := filepath.Join(".", kbDirName)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "创建目录失败: %v\n", err)
		os.Exit(1)
	}

	indexPath := filepath.Join(dir, indexFile)
	if _, err := os.Stat(indexPath); err == nil {
		fmt.Println("✅ 知识库已存在，跳过初始化。")
		return
	}

	content := `# Knowledge Index

> 项目可复用知识条目索引。每次增量开发后更新。
> 最后更新: ` + time.Now().Format("2006-01-02") + `

| 条目 | 标签 | 来源 | 更新日期 |
|------|------|------|----------|
`

	if err := os.WriteFile(indexPath, []byte(content), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "写入索引文件失败: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("✅ 知识库已初始化: %s\n", dir)
}

// ---------- reindex ----------

// runReindex 从 project-knowledge/ 下的内容文件重建 INDEX.md.
func runReindex() {
	entries, err := loadAllEntries()
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ 加载知识库失败: %v\n", err)
		os.Exit(1)
	}

	if len(entries) == 0 {
		fmt.Println("📚 知识库为空，INDEX.md 无需更新。")
		return
	}

	kbDir := filepath.Join(".", kbDirName)
	dateStr := time.Now().Format("2006-01-02")
	var b strings.Builder
	b.WriteString("# Knowledge Index\n\n")
	b.WriteString("> 项目可复用知识条目索引。每次增量开发后更新。\n")
	b.WriteString("> 最后更新: " + dateStr + "\n\n")
	b.WriteString("| 条目 | 标签 | 来源 | 更新日期 |\n")
	b.WriteString("|------|------|------|----------|\n")
	for _, e := range entries {
		b.WriteString(fmt.Sprintf("| %s | %s | %s | %s |\n", e.Title, strings.Join(e.Tags, ", "), e.Source, e.UpdatedAt))
	}

	indexPath := filepath.Join(kbDir, indexFile)
	if err := os.WriteFile(indexPath, []byte(b.String()), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "❌ 写入索引文件失败: %v\n", err)
		os.Exit(1)
	}

	appendLog(kbDir, "reindex", fmt.Sprintf("重建索引（%d条）", len(entries)), "all")
	fmt.Printf("✅ INDEX.md 已重建（共 %d 条）: %s\n", len(entries), indexPath)
}

// ---------- scan ----------

// scanCandidate 表示从代码中扫描出的候选知识条目.
type scanCandidate struct {
	Name    string // 函数名
	Doc     string // GoDoc 注释
	Pkg     string // 所在包名
	File    string // 文件路径
}

// runScan 扫描指定目录中的 Go 代码，提取导出函数/类型作为候选知识条目.
func runScan(args []string) {
	dirs := args
	if len(dirs) == 0 {
		dirs = []string{".", "pkg", "internal"}
	}

	// 收集候选
	var candidates []scanCandidate
	fset := token.NewFileSet()
	for _, dir := range dirs {
		if info, err := os.Stat(dir); err != nil || !info.IsDir() {
			continue // 不存在或不是目录则跳过
		}
		filepath.WalkDir(dir, func(path string, d fs.DirEntry, err error) error {
			if err != nil || d.IsDir() || !strings.HasSuffix(path, ".go") || strings.HasSuffix(path, "_test.go") {
				return nil
			}
			f, err := parser.ParseFile(fset, path, nil, parser.ParseComments)
			if err != nil {
				return nil // 跳过无法解析的文件
			}
			for _, decl := range f.Decls {
				fn, ok := decl.(*ast.FuncDecl)
				if !ok || !fn.Name.IsExported() {
					continue
				}
				// 跳过 main/init
				if fn.Name.Name == "main" || fn.Name.Name == "init" {
					continue
				}
				doc := ""
				if fn.Doc != nil {
					doc = strings.TrimSpace(fn.Doc.Text())
				}
				candidates = append(candidates, scanCandidate{
					Name: fn.Name.Name,
					Doc:  doc,
					Pkg:  f.Name.Name,
					File: path,
				})
			}
			return nil
		})
	}

	if len(candidates) == 0 {
		fmt.Println("🔍 未找到可导出的函数或类型。")
		return
	}

	// 加载已有条目，用于去重
	existing := make(map[string]bool)
	if entries, err := loadAllEntries(); err == nil {
		for _, e := range entries {
			existing[e.Title] = true
		}
	}

	// 过滤并输出
	newCount := 0
	for _, c := range candidates {
		title := c.Name
		if c.Doc != "" {
			// 用 GoDoc 首行作为简述
			shortDesc := c.Doc
			if idx := strings.Index(shortDesc, "\n"); idx > 0 {
				shortDesc = shortDesc[:idx]
			}
			title = fmt.Sprintf("[%s] %s - %s", c.Pkg, c.Name, shortDesc)
		}
		if existing[title] || existing[c.Name] {
			continue // 已存在，跳过
		}
		newCount++
		fmt.Printf("  📦 建议添加:\n")
		fmt.Printf("     knowledge add -t %q -s %q -p %q\n", title, c.File, firstLine(c.Doc))
		fmt.Println()
	}

	if newCount == 0 {
		fmt.Println("✅ 所有导出函数已存在于知识库，无需新增。")
	} else {
		fmt.Printf("📊 共发现 %d 个新候选条目（共扫描 %d 个导出函数）。\n", newCount, len(candidates))
		fmt.Println("💡 复制上方 knowledge add 命令执行即可保存。")
	}
}

// firstLine 返回文本的第一行，如为空则返回空字符串.
func firstLine(s string) string {
	s = strings.TrimSpace(s)
	if idx := strings.IndexByte(s, '\n'); idx >= 0 {
		return s[:idx]
	}
	return s
}

// ---------- add ----------

// stringSliceFlag implements flag.Value for repeated -r flags.
type stringSliceFlag struct {
	values *[]string
}

func (f *stringSliceFlag) String() string {
	if f.values == nil {
		return ""
	}
	return strings.Join(*f.values, ", ")
}

func (f *stringSliceFlag) Set(value string) error {
	*f.values = append(*f.values, value)
	return nil
}

// splitCommaList 以逗号（中英文）分隔字符串列表，每项 trim 空格.
// 不以空格分隔，因为条目 title 可能含空格（如 "FilterUtils - 过滤"）.
func splitCommaList(s string) []string {
	result := strings.FieldsFunc(s, func(r rune) bool {
		return r == ',' || r == '，'
	})
	// trim each item and filter empty
	filtered := []string{}
	for _, item := range result {
		trimmed := strings.TrimSpace(item)
		if trimmed != "" {
			filtered = append(filtered, trimmed)
		}
	}
	return filtered
}

// runAdd 交互式或命令行方式添加知识条目到知识库.
func runAdd(args []string) {
	title := ""
	source := ""
	purpose := ""
	example := ""
	format := "markdown" // 默认兼容旧格式
	interactiveTags := ""
	var relatedList []string

	fs := flag.NewFlagSet("add", flag.ExitOnError)
	fs.StringVar(&title, "t", "", "条目标题")
	fs.StringVar(&source, "s", "", "来源文件路径")
	fs.StringVar(&purpose, "p", "", "用途描述")
	fs.StringVar(&example, "e", "", "示例代码")
	fs.StringVar(&format, "format", "markdown", "条目格式: markdown（默认）或 yaml")
	fs.Var(&stringSliceFlag{&relatedList}, "r", "关联条目标题列表（逗号分隔或多次指定）")
	_ = fs.Parse(args)

	// 验证 format 参数
	if format != "markdown" && format != "yaml" {
		fmt.Fprintln(os.Stderr, "❌ --format 只接受 markdown 或 yaml")
		os.Exit(1)
	}

	// 交互模式
	if title == "" {
		reader := bufio.NewReader(os.Stdin)
		fmt.Print("📝 标题: ")
		title, _ = reader.ReadString('\n')
		title = strings.TrimSpace(title)

		fmt.Print("🏷️  标签(逗号分隔): ")
		interactiveTags, _ = reader.ReadString('\n')
		interactiveTags = strings.TrimSpace(interactiveTags)

		fmt.Print("📁 来源文件: ")
		source, _ = reader.ReadString('\n')
		source = strings.TrimSpace(source)

		fmt.Print("💡 用途: ")
		purpose, _ = reader.ReadString('\n')
		purpose = strings.TrimSpace(purpose)

		fmt.Print("🔧 示例代码(多行，EOF结束):\n")
		var lines []string
		for {
			line, err := reader.ReadString('\n')
			if err != nil {
				break
			}
			trimmed := strings.TrimSpace(line)
			if trimmed == "EOF" {
				break
			}
			lines = append(lines, line)
		}
		example = strings.TrimSpace(strings.Join(lines, ""))
	}

	if title == "" {
		fmt.Fprintln(os.Stderr, "❌ 标题不能为空")
		os.Exit(1)
	}

	// 生成条目
	now := time.Now()
	dateStr := now.Format("2006-01-02")
	id := fmt.Sprintf("entry-%d", now.Unix())
	// 确定标签：优先使用交互输入的标签，否则从标题的 [xxx] 前缀提取
	var tagList []string
	if interactiveTags != "" {
		tagList = strings.FieldsFunc(interactiveTags, func(r rune) bool {
			return r == ',' || r == '，' || r == ' '
		})
	}
	if len(tagList) == 0 {
		tagList = extractTags(title)
	}
	tagLine := strings.Join(tagList, ", ")
	if tagLine == "" {
		tagLine = "general"
	}

	var entry string
	if format == "yaml" {
		// YAML frontmatter 格式
		entry = formatYAMLEntry(id, title, tagList, source, dateStr, purpose, example, relatedList)
	} else {
		// Markdown 字段格式（默认，兼容旧项目）
		entry = formatMarkdownEntry(id, title, tagLine, source, dateStr, purpose, example, relatedList)
	}

	// 写入知识库文件
	kbDir := filepath.Join(".", kbDirName)
	if err := os.MkdirAll(kbDir, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "❌ 创建知识库目录失败: %v\n", err)
		os.Exit(1)
	}

	// 根据第一个标签选择子文件（避免逗号导致文件名错误）
	fileName := "common-utils.md"
	for _, t := range tagList {
		if t != "" {
			fileName = sanitizeFileName(t) + ".md"
			break
		}
	}
	filePath := filepath.Join(kbDir, fileName)

	f, err := os.OpenFile(filePath, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ 写入文件失败: %v\n", err)
		os.Exit(1)
	}
	defer f.Close()

	if _, err := f.WriteString(entry); err != nil {
		fmt.Fprintf(os.Stderr, "❌ 写入内容失败: %v\n", err)
		os.Exit(1)
	}

	// 更新 INDEX.md
	updateIndex(kbDir, title, tagLine, source, dateStr)

	// 写入操作日志 log.md
	appendLog(kbDir, "add", title, format)

	fmt.Printf("✅ 已保存条目 (%s格式): %s → %s\n", format, title, filePath)
}

// formatMarkdownEntry 生成 Markdown 字段格式的知识条目（兼容旧项目）.
func formatMarkdownEntry(id, title, tagLine, source, dateStr, purpose, example string, related []string) string {
	var b strings.Builder
	b.WriteString(fmt.Sprintf("\n<!-- id: %s -->\n", id))
	b.WriteString(fmt.Sprintf("## %s\n\n", title))
	b.WriteString(fmt.Sprintf("**标签**: %s\n", tagLine))
	b.WriteString(fmt.Sprintf("**来源**: %s\n", source))
	b.WriteString(fmt.Sprintf("**更新**: %s\n", dateStr))
	b.WriteString(fmt.Sprintf("**用途**: %s\n", purpose))
	if len(related) > 0 {
		b.WriteString(fmt.Sprintf("**关联**: %s\n", strings.Join(related, ", ")))
	}
	b.WriteString("\n")
	if example != "" {
		b.WriteString("```go\n")
		b.WriteString(example + "\n")
		b.WriteString("```\n")
	}
	b.WriteString("\n---\n")
	return b.String()
}

// formatYAMLEntry 生成 YAML frontmatter 格式的知识条目（推荐新条目使用）.
func formatYAMLEntry(id, title string, tags []string, source, dateStr, purpose, example string, related []string) string {
	// 从标题中剥离 [tag] 前缀，因为标签已在 tags 字段中单独记录
	pureTitle := stripTagPrefix(title)

	var b strings.Builder
	b.WriteString("---\n")
	b.WriteString(fmt.Sprintf("id: %s\n", id))
	b.WriteString(fmt.Sprintf("title: \"%s\"\n", escapeYAMLString(pureTitle)))
	b.WriteString(fmt.Sprintf("tags: [%s]\n", strings.Join(tags, ", ")))
	b.WriteString(fmt.Sprintf("source: \"%s\"\n", escapeYAMLString(source)))
	b.WriteString(fmt.Sprintf("updated: %s\n", dateStr))
	b.WriteString(fmt.Sprintf("purpose: \"%s\"\n", escapeYAMLString(purpose)))
	if len(related) > 0 {
		b.WriteString(fmt.Sprintf("related: [%s]\n", strings.Join(related, ", ")))
	}
	b.WriteString("---\n\n")
	if example != "" {
		b.WriteString("```go\n")
		b.WriteString(example + "\n")
		b.WriteString("```\n\n")
	}
	b.WriteString("---\n")
	return b.String()
}

// stripTagPrefix 从标题中剥离 [xxx] 标签前缀，返回纯标题.
func stripTagPrefix(title string) string {
	re := regexp.MustCompile(`^\[[^\]]+\]\s*`)
	return re.ReplaceAllString(title, "")
}

// escapeYAMLString 对 YAML 字符串值进行转义，处理引号和特殊字符.
func escapeYAMLString(s string) string {
	s = strings.ReplaceAll(s, "\"", "\\\"")
	s = strings.ReplaceAll(s, "\n", "\\n")
	return s
}

// appendLog 将操作追加到 log.md.
func appendLog(kbDir, action, detail, format string) {
	logPath := filepath.Join(kbDir, logFile)
	timestamp := time.Now().Format("2006-01-02 15:04:05")
	logLine := fmt.Sprintf("| %s | %s | %s | %s |\n", timestamp, action, detail, format)

	// 如果 log.md 不存在，创建带表头的文件
	if _, err := os.Stat(logPath); os.IsNotExist(err) {
		header := "# Knowledge Operation Log\n\n> 知识库操作日志，每次 add/reindex/lint 操作自动追加。\n\n| 时间 | 操作 | 详情 | 格式 |\n|------|------|------|------|\n"
		if err := os.WriteFile(logPath, []byte(header), 0o644); err != nil {
			fmt.Fprintf(os.Stderr, "警告: 创建日志文件失败: %v\n", err)
			return
		}
	}

	f, err := os.OpenFile(logPath, os.O_APPEND|os.O_WRONLY, 0o644)
	if err != nil {
		fmt.Fprintf(os.Stderr, "警告: 写入日志文件失败: %v\n", err)
		return
	}
	defer f.Close()

	if _, err := f.WriteString(logLine); err != nil {
		fmt.Fprintf(os.Stderr, "警告: 写入日志内容失败: %v\n", err)
	}
}

// extractTags 从 "[tag1, tag2] Title" 格式的标题中提取标签列表.
func extractTags(title string) []string {
	re := regexp.MustCompile(`\[([^\]]+)\]`)
	matches := re.FindStringSubmatch(title)
	if len(matches) > 1 {
		tagContent := strings.TrimSpace(matches[1])
		return strings.FieldsFunc(tagContent, func(r rune) bool {
			return r == ',' || r == '，' || r == ' '
		})
	}
	return nil
}

// updateIndex 将新增条目的摘要信息追加到 INDEX.md 索引表中.
func updateIndex(kbDir, title, tags, source, date string) {
	indexPath := filepath.Join(kbDir, indexFile)
	data, err := os.ReadFile(indexPath)
	if err != nil {
		return // 索引文件不存在时静默跳过
	}

	line := fmt.Sprintf("| %s | %s | %s | %s |", title, tags, source, date)
	lines := strings.Split(string(data), "\n")

	// 找到表格区域（从 |---|---|--- 到最后一条 | 行）
	tableStart := -1
	tableEnd := -1
	for i, l := range lines {
		if strings.HasPrefix(l, "|------") {
			tableStart = i
		}
		if tableStart != -1 && strings.HasPrefix(strings.TrimSpace(l), "|") {
			tableEnd = i // 持续更新到最后一条 | 行
		}
	}

	if tableStart == -1 || tableEnd == -1 {
		// 没有表格，直接追加
		lines = append(lines, line)
	} else {
		// 更新最后更新日期
		for i, l := range lines {
			if strings.HasPrefix(l, "> 最后更新:") {
				lines[i] = "> 最后更新: " + date
				break
			}
		}
		// 在表格最后一行后面插入
		newLines := make([]string, 0, len(lines)+1)
		newLines = append(newLines, lines[:tableEnd+1]...)
		newLines = append(newLines, line)
		newLines = append(newLines, lines[tableEnd+1:]...)
		lines = newLines
	}

	if err := os.WriteFile(indexPath, []byte(strings.Join(lines, "\n")), 0o644); err != nil {
		fmt.Fprintf(os.Stderr, "警告: 更新索引文件失败: %v\n", err)
	}
}

// sanitizeFileName 将标签转为安全的文件名（去特殊字符、小写、空格转下划线）.
func sanitizeFileName(tag string) string {
	safe := strings.Map(func(r rune) rune {
		if (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') || r == '-' || r == '_' {
			return r
		}
		if r == ' ' || r == '.' || r == '/' || r == '\\' {
			return '_'
		}
		return -1 // 删除
	}, strings.ToLower(tag))
	// 清理前导/尾随下划线并去除空白结果
	safe = strings.Trim(safe, "_")
	if safe == "" {
		return "untagged"
	}
	return safe
}

// ---------- search ----------

// runSearch 全文搜索知识库，按相关性排序输出匹配条目.
func runSearch(args []string) {
	if len(args) == 0 {
		fmt.Fprintln(os.Stderr, "❌ 请指定搜索关键词")
		os.Exit(1)
	}
	keyword := strings.ToLower(strings.Join(args, " "))

	entries, err := loadAllEntries()
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ 加载知识库失败: %v\n", err)
		os.Exit(1)
	}

	type scored struct {
		entry Entry
		score int
	}

	var results []scored
	for _, e := range entries {
		s := scoreEntry(e, keyword)
		if s > 0 {
			results = append(results, scored{e, s})
		}
	}

	if len(results) == 0 {
		fmt.Println("❌ 未找到匹配条目。")
		return
	}

	// 按分数排序
	sort.Slice(results, func(i, j int) bool {
		return results[i].score > results[j].score
	})

	fmt.Printf("🔍 找到 %d 条匹配结果:\n\n", len(results))
	for i, r := range results {
		e := r.entry
		fmt.Printf("%d. [%s](%s:%d)\n", i+1, e.Title, e.FilePath, e.LineNum)
		fmt.Printf("   📁 %s\n", e.Source)
		fmt.Printf("   🏷️  %s\n", strings.Join(e.Tags, ", "))
		fmt.Printf("   💡 %s\n", e.Purpose)
		if len(e.Related) > 0 {
			fmt.Printf("   🔗 关联: %s\n", strings.Join(e.Related, ", "))
		}
		fmt.Printf("   📅 %s\n\n", e.UpdatedAt)
	}
}

// scoreEntry 对知识条目按关键词进行加权评分。（标题30 > 标签8 > 用途5 > 来源3 > 示例2）.
func scoreEntry(e Entry, keyword string) int {
	score := 0
	kw := strings.ToLower(keyword)

	// 标题匹配（最高权重）
	if strings.Contains(strings.ToLower(e.Title), kw) {
		score += 10
		if strings.EqualFold(e.Title, kw) {
			score += 20 // 完全匹配
		}
	}

	// 标签匹配
	for _, tag := range e.Tags {
		if strings.Contains(strings.ToLower(tag), kw) {
			score += 8
		}
	}

	// 用途描述匹配
	if strings.Contains(strings.ToLower(e.Purpose), kw) {
		score += 5
	}

	// 来源文件匹配
	if strings.Contains(strings.ToLower(e.Source), kw) {
		score += 3
	}

	// 示例代码匹配
	if strings.Contains(strings.ToLower(e.Example), kw) {
		score += 2
	}

	return score
}

// ---------- list ----------

// runList 列出知识库中所有条目，支持 --stale 过滤过时条目.
func runList(args []string) {
	checkStale := false
	var projectDir string

	fs := flag.NewFlagSet("list", flag.ExitOnError)
	fs.BoolVar(&checkStale, "stale", false, "同时检查过期条目")
	_ = fs.Parse(args)

	if checkStale && len(fs.Args()) > 0 {
		projectDir = fs.Args()[0]
	}

	entries, err := loadAllEntries()
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ 加载知识库失败: %v\n", err)
		os.Exit(1)
	}

	if len(entries) == 0 {
		fmt.Println("📚 知识库为空。使用 `knowledge add` 添加条目。")
		return
	}

	fmt.Printf("📚 知识库共 %d 条:\n\n", len(entries))
	for i, e := range entries {
		fmt.Printf("%d. %s\n", i+1, e.Title)
		fmt.Printf("   📁 %s | 🏷️  %s | 📅 %s\n", e.Source, strings.Join(e.Tags, ", "), e.UpdatedAt)
		if checkStale && projectDir != "" {
			status := checkEntryFreshness(e, projectDir)
			fmt.Printf("   %s\n", status)
		}
		fmt.Println()
	}
}

// ---------- check-stale ----------

// runCheckStale 对比知识条目来源文件的修改时间，报告过期条目.
func runCheckStale(args []string) {
	if len(args) == 0 {
		fmt.Fprintln(os.Stderr, "❌ 请指定项目代码目录路径")
		fmt.Println("用法: knowledge check-stale <项目目录>")
		os.Exit(1)
	}
	projectDir := args[0]

	entries, err := loadAllEntries()
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ 加载知识库失败: %v\n", err)
		os.Exit(1)
	}

	if len(entries) == 0 {
		fmt.Println("📚 知识库为空，无需检查。")
		return
	}

	staleCount := 0
	freshCount := 0

	fmt.Println("🔍 正在检查条目时效性...")
	for _, e := range entries {
		status := checkEntryFreshness(e, projectDir)
		if strings.Contains(status, "过期") || strings.Contains(status, "可能过期") {
			staleCount++
			fmt.Printf("⚠️  %s\n", status)
			fmt.Printf("   📁 来源: %s | 📅 记录: %s\n", e.Source, e.UpdatedAt)
			fmt.Println()
		} else {
			freshCount++
		}
	}

	fmt.Printf("📊 结果: %d 条有效, %d 条过期/待更新\n", freshCount, staleCount)
	if staleCount > 0 {
		fmt.Println("💡 提示: 使用 `knowledge add` 重新录入过期条目以更新信息。")
	}
}

// checkEntryFreshness 对比条目来源文件的修改时间与记录日期，返回时效状态字符串.
func checkEntryFreshness(e Entry, projectDir string) string {
	if e.Source == "" || e.Source == "-" {
		return fmt.Sprintf("✅ %s 无来源文件，持保留", e.Title)
	}

	sourcePath := filepath.Join(projectDir, e.Source)
	info, err := os.Stat(sourcePath)
	if err != nil {
		return fmt.Sprintf("⚠️  [%s] 来源文件不存在: %s", e.Title, e.Source)
	}

	modTime := info.ModTime()
	entryTime, err := time.Parse("2006-01-02", e.UpdatedAt)
	if err != nil {
		return fmt.Sprintf("⚠️  [%s] 日期格式无法解析: %s", e.Title, e.UpdatedAt)
	}

	if modTime.After(entryTime.Add(24 * time.Hour)) {
		return fmt.Sprintf("⚠️  [%s] 可能过期 — 文件 %s 最后修改 %s，条目记录 %s",
			e.Title, e.Source, modTime.Format("2006-01-02"), e.UpdatedAt)
	}

	return fmt.Sprintf("✅ [%s] 时效正常", e.Title)
}

// ---------- 知识库加载 ----------

// loadAllEntries 遍历 project-knowledge/ 目录，解析所有 .md 文件并返回条目列表.
func loadAllEntries() ([]Entry, error) {
	kbDir := filepath.Join(".", kbDirName)
	if _, err := os.Stat(kbDir); os.IsNotExist(err) {
		return nil, fmt.Errorf("知识库目录不存在 (%s)，请先运行 `knowledge init`", kbDir)
	}

	var entries []Entry
	err := filepath.WalkDir(kbDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if d.IsDir() || !strings.HasSuffix(d.Name(), ".md") || d.Name() == indexFile {
			return nil
		}

		fileEntries, err := parseEntries(path)
		if err != nil {
			return err
		}
		entries = append(entries, fileEntries...)
		return nil
	})

	if err != nil {
		return nil, err
	}

	return entries, nil
}

// parseEntries 解析单个 .md 知识文件，提取所有结构化 Entry.
// 支持两种格式：Markdown 字段格式和 YAML frontmatter 格式（向后兼容）.
func parseEntries(path string) ([]Entry, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	content := string(data)

	// 检测是否包含 YAML frontmatter
	if strings.HasPrefix(content, "---\n") {
		return parseYAMLEntries(content, path)
	}

	return parseMarkdownEntries(content, path)
}

// parseYAMLEntries 解析包含 YAML frontmatter 的知识文件.
func parseYAMLEntries(content, path string) ([]Entry, error) {
	lines := strings.Split(content, "\n")
	var entries []Entry
	var current *Entry
	inCodeBlock := false
	inYAMLBlock := false
	yamlLines := []string{}
	contentAfterYAML := []string{}
	yamlEndIdx := -1

	// 先找到 YAML 块的结束位置（第二个 ---）
	for i, line := range lines {
		trimmed := strings.TrimSpace(line)
		if i == 0 && yamlDelimRe.MatchString(trimmed) {
			inYAMLBlock = true
			continue
		}
		if inYAMLBlock && yamlDelimRe.MatchString(trimmed) {
			inYAMLBlock = false
			yamlEndIdx = i
			break
		}
		if inYAMLBlock {
			yamlLines = append(yamlLines, line)
		}
	}

	// 解析 YAML 字段为 Entry
	if len(yamlLines) > 0 {
		current = parseYAMLFields(yamlLines)
		if current != nil {
			current.FilePath = path
			current.Format = "yaml"
		}
	}

	// 解析 YAML 之后的内容（示例代码等）
	if yamlEndIdx >= 0 {
		for i := yamlEndIdx + 1; i < len(lines); i++ {
			contentAfterYAML = append(contentAfterYAML, lines[i])
		}
	}

	// 解析后续内容中的示例代码
	if current != nil && len(contentAfterYAML) > 0 {
		inCodeBlock = false
		for _, line := range contentAfterYAML {
			trimmed := strings.TrimSpace(line)
			if strings.HasPrefix(trimmed, "```") {
				inCodeBlock = !inCodeBlock
				continue
			}
			if inCodeBlock {
				current.Example += line + "\n"
			}
			// 遇到第二个 --- 分隔符，表示条目结束
			if trimmed == "---" && !inCodeBlock {
				current.Example = strings.TrimSpace(current.Example)
				entries = append(entries, *current)
				current = nil
			}
		}
		if current != nil {
			current.Example = strings.TrimSpace(current.Example)
			entries = append(entries, *current)
		}
	}

	// 检查是否有更多 YAML frontmatter 条目（多个 --- 块）
	// 继续从 yamlEndIdx+1 之后扫描，找下一个 --- 块
	if yamlEndIdx >= 0 && len(contentAfterYAML) > 0 {
		remaining := strings.Join(contentAfterYAML, "\n")
		// 递归检查是否有后续 YAML 块
		subEntries, err := parseEntriesFromRemaining(remaining, path)
		if err == nil && len(subEntries) > 0 {
			// 排除已处理的第一个条目后的重复
			alreadyCounted := 0
			if len(entries) > 0 {
				alreadyCounted = 1
			}
			if len(subEntries) > alreadyCounted {
				entries = append(entries, subEntries[alreadyCounted:]...)
			}
		}
	}

	return entries, nil
}

// parseEntriesFromRemaining 从剩余内容中解析条目（用于多 YAML 块文件）.
func parseEntriesFromRemaining(content, path string) ([]Entry, error) {
	// 如果内容以 --- 开始，说明有更多 YAML 块
	if strings.HasPrefix(strings.TrimSpace(content), "---\n") ||
		strings.HasPrefix(strings.TrimSpace(content), "---") {
		return parseYAMLEntries(content, path)
	}
	// 否则可能是 Markdown 格式的后续内容
	return parseMarkdownEntries(content, path)
}

// parseYAMLFields 从 YAML 行列表中解析 Entry 字段.
func parseYAMLFields(yamlLines []string) *Entry {
	entry := &Entry{}
	for _, line := range yamlLines {
		matches := yamlFieldRe.FindStringSubmatch(strings.TrimSpace(line))
		if len(matches) < 3 {
			continue
		}
		key := matches[1]
		value := strings.TrimSpace(matches[2])

		switch key {
		case "id":
			entry.ID = value
		case "title":
			entry.Title = unescapeYAMLString(strings.Trim(value, "\""))
		case "tags":
			// 解析 [tag1, tag2] 格式
			if arrMatches := yamlArrayRe.FindStringSubmatch(value); len(arrMatches) > 1 {
				entry.Tags = strings.FieldsFunc(arrMatches[1], func(r rune) bool {
					return r == ',' || r == ' '
				})
			} else {
				// 单个标签或逗号分隔
				entry.Tags = strings.FieldsFunc(value, func(r rune) bool {
					return r == ',' || r == ' '
				})
			}
		case "source":
			entry.Source = unescapeYAMLString(strings.Trim(value, "\""))
		case "updated":
			entry.UpdatedAt = value
		case "purpose":
			entry.Purpose = unescapeYAMLString(strings.Trim(value, "\""))
		case "related":
			// 解析 [title1, title2] 格式 — 只以逗号分隔，因为 title 可能含空格
			if arrMatches := yamlArrayRe.FindStringSubmatch(value); len(arrMatches) > 1 {
				entry.Related = splitCommaList(arrMatches[1])
			} else {
				entry.Related = splitCommaList(value)
			}
		}
	}
	return entry
}

// unescapeYAMLString 对 YAML 字符串值进行反转义.
func unescapeYAMLString(s string) string {
	s = strings.ReplaceAll(s, "\\\"", "\"")
	s = strings.ReplaceAll(s, "\\n", "\n")
	return s
}

// parseMarkdownEntries 解析 Markdown 字段格式的知识文件（旧格式兼容）.
func parseMarkdownEntries(content, path string) ([]Entry, error) {
	lines := strings.Split(content, "\n")
	var entries []Entry
	var current *Entry
	inCodeBlock := false

	for i, line := range lines {
		trimmed := strings.TrimSpace(line)

		// 跳过代码块
		if strings.HasPrefix(trimmed, "```") {
			inCodeBlock = !inCodeBlock
			if current != nil && inCodeBlock {
				// 进入代码块，开始收集示例代码
			}
			continue
		}

		if inCodeBlock {
			if current != nil {
				current.Example += line + "\n"
			}
			continue
		}

		// 解析元数据注释
		if matches := metaRe.FindStringSubmatch(line); len(matches) > 0 {
			key := matches[1]
			value := strings.TrimSpace(matches[2])
			switch key {
			case "id":
				if current != nil {
					entries = append(entries, *current)
				}
				current = &Entry{ID: value, FilePath: path, LineNum: i + 1, Format: "markdown"}
			}
			continue
		}

		// 解析标题（作为条目的隐式开始）
		if matches := titleRe.FindStringSubmatch(trimmed); len(matches) > 0 && !strings.HasPrefix(trimmed, "```") {
			if current != nil && current.ID == "" {
				// 上一个条目没有 id，保存它（通过隐式标题开始的条目）
				entries = append(entries, *current)
				current = nil
			}
			if current == nil {
				current = &Entry{Title: matches[2], FilePath: path, LineNum: i + 1, Format: "markdown"}
			} else {
				// current 已有 ID（来自元数据注释），只更新标题
				current.Title = matches[2]
			}

			// 提取标签前缀 [xxx]
			if tagPrefix := matches[1]; tagPrefix != "" {
				tag := strings.TrimSpace(strings.Trim(tagPrefix, "[]"))
				current.Tags = strings.FieldsFunc(tag, func(r rune) bool {
					return r == ',' || r == '，' || r == ' '
				})
			}
			continue
		}

		if current == nil {
			continue
		}

		// 解析字段
		if matches := fieldRe.FindStringSubmatch(trimmed); len(matches) > 0 {
			fieldName := matches[1]
			fieldValue := strings.TrimSpace(matches[2])
			switch fieldName {
			case "标签":
				current.Tags = strings.FieldsFunc(fieldValue, func(r rune) bool {
					return r == ',' || r == '，' || r == ' '
				})
			case "来源":
				current.Source = fieldValue
			case "更新":
				current.UpdatedAt = fieldValue
			case "用途":
				current.Purpose = fieldValue
			case "关联":
				current.Related = splitCommaList(fieldValue)
			}
			continue
		}
	}

	if current != nil {
		entries = append(entries, *current)
	}

	return entries, nil
}

// ---------- link ----------

// discoverImportRelations 通过分析条目来源文件的 import 语句，发现条目间的依赖关系.
// 仅分析 Go 源码的 import 声明.
func discoverImportRelations(entries []Entry, projectDir string) map[string][]string {
	relations := make(map[string][]string)

	// 构建 source → entry 映射
	sourceToEntries := make(map[string][]Entry)
	for _, e := range entries {
		if e.Source != "" && e.Source != "-" {
			sourceToEntries[e.Source] = append(sourceToEntries[e.Source], e)
		}
	}

	fset := token.NewFileSet()
	for _, e := range entries {
		if e.Source == "" || e.Source == "-" {
			continue
		}
		sourcePath := filepath.Join(projectDir, e.Source)
		if _, err := os.Stat(sourcePath); err != nil {
			continue
		}

		f, err := parser.ParseFile(fset, sourcePath, nil, parser.ImportsOnly)
		if err != nil {
			continue
		}

		for _, imp := range f.Imports {
			// import "pkg/search" → 尝试匹配 source 为 pkg/search.go 的条目
			importPath := strings.Trim(imp.Path.Value, "\"")
			importFile := importPath + ".go"
			importBasename := filepath.Base(importPath) + ".go"

			for srcKey, srcEntries := range sourceToEntries {
				if strings.HasSuffix(srcKey, importFile) || strings.HasSuffix(srcKey, importBasename) || filepath.Base(srcKey) == importBasename {
					for _, se := range srcEntries {
						if se.Title != e.Title {
							relations[e.Title] = append(relations[e.Title], se.Title)
						}
					}
				}
			}
		}
	}

	// Deduplicate
	for k, v := range relations {
		seen := make(map[string]bool)
		deduped := []string{}
		for _, s := range v {
			if !seen[s] {
				seen[s] = true
				deduped = append(deduped, s)
			}
		}
		relations[k] = deduped
	}

	return relations
}

// discoverTagRelations 通过标签相似度发现条目间的关联关系.
// 当两个条目共享 >= minShared 个标签时，认为它们关联.
func discoverTagRelations(entries []Entry, minShared int) map[string][]string {
	relations := make(map[string][]string)

	for i, e1 := range entries {
		e1Tags := make(map[string]bool)
		for _, t := range e1.Tags {
			e1Tags[t] = true
		}
		for j, e2 := range entries {
			if i == j {
				continue
			}
			shared := 0
			for _, t := range e2.Tags {
				if e1Tags[t] {
					shared++
				}
			}
			if shared >= minShared {
				relations[e1.Title] = append(relations[e1.Title], e2.Title)
			}
		}
	}

	return relations
}

// runLink 自动发现条目间的关联关系并输出建议.
func runLink(args []string) {
	projectDir := "."
	if len(args) > 0 {
		projectDir = args[0]
	}

	entries, err := loadAllEntries()
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ 加载知识库失败: %v\n", err)
		os.Exit(1)
	}

	if len(entries) == 0 {
		fmt.Println("📚 知识库为空，无法发现关联。")
		return
	}

	// 1. import 分析
	importRelations := discoverImportRelations(entries, projectDir)

	// 2. 标签相似度
	tagRelations := discoverTagRelations(entries, 2)

	// 合并并去重（排除已存在的关联）
	existingRelated := make(map[string]map[string]bool)
	for _, e := range entries {
		m := make(map[string]bool)
		for _, r := range e.Related {
			m[r] = true
		}
		existingRelated[e.Title] = m
	}

	totalSuggestions := 0
	for _, e := range entries {
		suggestions := []string{}

		// import 关联
		if refs, ok := importRelations[e.Title]; ok {
			for _, ref := range refs {
				if !existingRelated[e.Title][ref] {
					suggestions = append(suggestions, ref)
				}
			}
		}

		// 标签关联
		if refs, ok := tagRelations[e.Title]; ok {
			for _, ref := range refs {
				if !existingRelated[e.Title][ref] {
					already := false
					for _, s := range suggestions {
						if s == ref {
							already = true
							break
						}
					}
					if !already {
						suggestions = append(suggestions, ref)
					}
				}
			}
		}

		if len(suggestions) == 0 {
			continue
		}

		totalSuggestions += len(suggestions)
		fmt.Printf("🔗 %s\n", e.Title)
		fmt.Printf("   建议关联: %s\n", strings.Join(suggestions, ", "))
		fmt.Printf("   添加命令: knowledge add -t %q -s %q -p %q -r %s\n",
			e.Title, e.Source, e.Purpose, strings.Join(suggestions, ","))
		fmt.Println()
	}

	if totalSuggestions == 0 {
		fmt.Println("✅ 未发现新的关联建议（所有 import 和标签关联已记录）。")
	} else {
		fmt.Printf("📊 共发现 %d 个关联建议。\n", totalSuggestions)
		fmt.Println("💡 复制上方 knowledge add 命令并添加 -r 参数即可更新条目关联。")
	}
}

// ---------- lint ----------

// LintIssue 表示 lint 检查发现的问题.
type LintIssue struct {
	Level   string // "error" 或 "warning"
	Message string
	Entry   string // 相关条目的标题
}

// runLint 执行知识库完整性检查.
func runLint(args []string) {
	kbDir := filepath.Join(".", kbDirName)
	if _, err := os.Stat(kbDir); os.IsNotExist(err) {
		fmt.Fprintln(os.Stderr, "❌ 知识库目录不存在，请先运行 `knowledge init`")
		os.Exit(1)
	}

	entries, err := loadAllEntries()
	if err != nil {
		fmt.Fprintf(os.Stderr, "❌ 加载知识库失败: %v\n", err)
		os.Exit(1)
	}

	if len(entries) == 0 {
		fmt.Println("📚 知识库为空，无需 lint 检查。")
		return
	}

	var issues []LintIssue

	// 1. 检查重复标题
	titleCount := make(map[string]int)
	for _, e := range entries {
		titleCount[e.Title]++
	}
	for title, count := range titleCount {
		if count > 1 {
			issues = append(issues, LintIssue{
				Level:   "error",
				Message: fmt.Sprintf("标题重复 %d 次", count),
				Entry:   title,
			})
		}
	}

	// 2. 检查弱标签（只有 general 或空标签）
	for _, e := range entries {
		if len(e.Tags) == 0 {
			issues = append(issues, LintIssue{
				Level:   "warning",
				Message: "无标签",
				Entry:   e.Title,
			})
		} else if len(e.Tags) == 1 && e.Tags[0] == "general" {
			issues = append(issues, LintIssue{
				Level:   "warning",
				Message: "仅有 general 标签，建议添加更具描述性的标签",
				Entry:   e.Title,
			})
		}
	}

	// 3. 检查过旧条目（超过 90 天未更新）
	staleThreshold := 90 * 24 * time.Hour
	now := time.Now()
	for _, e := range entries {
		if e.UpdatedAt == "" {
			issues = append(issues, LintIssue{
				Level:   "warning",
				Message: "无更新日期",
				Entry:   e.Title,
			})
			continue
		}
		entryTime, err := time.Parse("2006-01-02", e.UpdatedAt)
		if err != nil {
			issues = append(issues, LintIssue{
				Level:   "warning",
				Message: fmt.Sprintf("日期格式无法解析: %s", e.UpdatedAt),
				Entry:   e.Title,
			})
			continue
		}
		if now.Sub(entryTime) > staleThreshold {
			days := int(now.Sub(entryTime).Hours() / 24)
			issues = append(issues, LintIssue{
				Level:   "warning",
				Message: fmt.Sprintf("超过 %d 天未更新（最后更新: %s）", days, e.UpdatedAt),
				Entry:   e.Title,
			})
		}
	}

	// 4. 检查 INDEX.md 与内容文件的一致性
	indexPath := filepath.Join(kbDir, indexFile)
	indexData, err := os.ReadFile(indexPath)
	if err != nil {
		issues = append(issues, LintIssue{
			Level:   "error",
			Message: "INDEX.md 不存在或无法读取",
			Entry:   "",
		})
	} else {
		// 检查 INDEX.md 中是否包含所有条目
		indexContent := string(indexData)
		for _, e := range entries {
			if !strings.Contains(indexContent, e.Title) {
				issues = append(issues, LintIssue{
					Level:   "warning",
					Message: "条目未出现在 INDEX.md 中（建议运行 knowledge reindex）",
					Entry:   e.Title,
				})
			}
		}
	}

	// 5. 检查空用途描述
	for _, e := range entries {
		if e.Purpose == "" {
			issues = append(issues, LintIssue{
				Level:   "warning",
				Message: "缺少用途描述",
				Entry:   e.Title,
			})
		}
	}

	// 6. 检查关联引用是否存在
	allTitles := make(map[string]bool)
	for _, e := range entries {
		allTitles[e.Title] = true
	}
	for _, e := range entries {
		for _, ref := range e.Related {
			if !allTitles[ref] {
				issues = append(issues, LintIssue{
					Level:   "error",
					Message: fmt.Sprintf("关联引用不存在: '%s'", ref),
					Entry:   e.Title,
				})
			}
		}
	}

	// 输出结果
	errorCount := 0
	warningCount := 0
	for _, issue := range issues {
		if issue.Level == "error" {
			errorCount++
		} else {
			warningCount++
		}
	}

	if len(issues) == 0 {
		fmt.Println("✅ 知识库 lint 检查通过，无问题。")
		appendLog(kbDir, "lint", "lint检查通过", "all")
		return
	}

	fmt.Printf("🔍 lint 检查发现 %d 个问题（%d error, %d warning）:\n\n", len(issues), errorCount, warningCount)
	for _, issue := range issues {
		icon := "⚠️"
		if issue.Level == "error" {
			icon = "❌"
		}
		entryInfo := ""
		if issue.Entry != "" {
			entryInfo = fmt.Sprintf(" [%s]", issue.Entry)
		}
		fmt.Printf("  %s %s%s: %s\n", icon, issue.Level, entryInfo, issue.Message)
	}

	if errorCount > 0 {
		fmt.Println("\n💡 建议优先修复 error 级别的问题。")
	}
	fmt.Println("\n💡 修复建议：")
	fmt.Println("  - 重复标题：使用 `knowledge add` 时确保标题唯一")
	fmt.Println("  - 索引不一致：运行 `knowledge reindex` 重建索引")
	fmt.Println("  - 过旧条目：运行 `knowledge check-stale <项目目录>` 检查来源文件变更")

	appendLog(kbDir, "lint", fmt.Sprintf("发现%d个问题（%d error, %d warning）", len(issues), errorCount, warningCount), "all")
}
