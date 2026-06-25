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
	"io/fs"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

const (
	kbDirName = "project-knowledge"
	indexFile = "INDEX.md"
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
}

var (
	// 元数据正则：<!-- key: value -->
	metaRe = regexp.MustCompile(`<!--\s*(\w[\w-]*)\s*:\s*(.*?)\s*-->`)
	// 标题正则：## [tag] Title
	titleRe = regexp.MustCompile(`^##\s+(\[[^\]]+\]\s*)?(.+)$`)
	// 字段正则：**字段名**: 值
	fieldRe = regexp.MustCompile(`^\*\*([^*]+)\*\*\s*:\s*(.+)$`)
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
	case "help", "--help", "-h":
		printUsage()
	default:
		fmt.Fprintf(os.Stderr, "未知命令: %s\n\n", cmd)
		printUsage()
		os.Exit(1)
	}
}

func printUsage() {
	fmt.Print(`Knowledge — 知识库管理工具

用法:
  knowledge init                   初始化知识库目录结构
  knowledge init --example         初始化知识库并导入示例条目（5条参考）
  knowledge add                   交互式添加知识条目
  knowledge add -t "标题" -s "来源" -p "用途" [-e "示例代码"]  命令行添加
  knowledge search <关键词>        搜索知识条目
  knowledge list                  列出所有条目
  knowledge list --stale <项目目录> 列出过时条目
  knowledge check-stale <项目目录>  检查并报告过期条目
  knowledge reindex                 从内容文件重建 INDEX.md
`)
}

// ---------- init ----------

func runInit(args []string) {
	withExample := false

	fs := flag.NewFlagSet("init", flag.ExitOnError)
	fs.BoolVar(&withExample, "example", false, "使用示例条目初始化知识库")
	_ = fs.Parse(args)

	dir := filepath.Join(".", kbDirName)
	if err := os.MkdirAll(dir, 0o755); err != nil {
		fmt.Fprintf(os.Stderr, "创建目录失败: %v\n", err)
		os.Exit(1)
	}

	indexPath := filepath.Join(dir, indexFile)
	if _, err := os.Stat(indexPath); err == nil {
		fmt.Println("知识库已存在，跳过初始化。")
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

	if withExample {
		examplePath := filepath.Join(dir, "common-utils.md")
		if err := os.WriteFile(examplePath, []byte(exampleContent()), 0o644); err != nil {
			fmt.Fprintf(os.Stderr, "写入示例文件失败: %v\n", err)
			os.Exit(1)
		}
		fmt.Println("📚 已导入 5 条示例条目，可用 `knowledge list` 查看。")
		fmt.Println("💡 参考文件: reference/project-knowledge-example.md")
	}
}

// ---------- reindex ----------

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

	fmt.Printf("✅ INDEX.md 已重建（共 %d 条）: %s\n", len(entries), indexPath)
}

// ---------- add ----------

func runAdd(args []string) {
	title := ""
	source := ""
	purpose := ""
	example := ""
	interactiveTags := ""

	fs := flag.NewFlagSet("add", flag.ExitOnError)
	fs.StringVar(&title, "t", "", "条目标题")
	fs.StringVar(&source, "s", "", "来源文件路径")
	fs.StringVar(&purpose, "p", "", "用途描述")
	fs.StringVar(&example, "e", "", "示例代码")
	_ = fs.Parse(args)

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

	entry := fmt.Sprintf("\n<!-- id: %s -->\n", id)
	entry += fmt.Sprintf("## %s\n\n", title)
	entry += fmt.Sprintf("**标签**: %s\n", tagLine)
	entry += fmt.Sprintf("**来源**: %s\n", source)
	entry += fmt.Sprintf("**更新**: %s\n", dateStr)
	entry += fmt.Sprintf("**用途**: %s\n\n", purpose)
	if example != "" {
		entry += "```go\n"
		entry += example + "\n"
		entry += "```\n"
	}
	entry += "\n---\n"

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

	fmt.Printf("✅ 已保存条目: %s → %s\n", title, filePath)
}

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

	_ = os.WriteFile(indexPath, []byte(strings.Join(lines, "\n")), 0o644)
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
		fmt.Printf("   📅 %s\n\n", e.UpdatedAt)
	}
}

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

func parseEntries(path string) ([]Entry, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}

	content := string(data)
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
				current = &Entry{ID: value, FilePath: path, LineNum: i + 1}
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
				current = &Entry{Title: matches[2], FilePath: path, LineNum: i + 1}
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
			}
			continue
		}
	}

	if current != nil {
		entries = append(entries, *current)
	}

	return entries, nil
}
