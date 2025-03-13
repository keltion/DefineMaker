package main

import (
	"bytes"
	"fmt"
	"os/exec"
	"regexp"
	"strings"
)

func parseRPCSignature(line string) (string, string, string, bool) {
	pattern := `rpc\s+(\w+)\s*\(\s*([\w.]+)\s*\)\s*returns\s*\(\s*([\w.]+)\s*\)`
	re := regexp.MustCompile(pattern)
	matches := re.FindStringSubmatch(line)

	if len(matches) == 4 {
		return matches[1], matches[2], matches[3], true
	}
	return "", "", "", false
}

func getLastCommitAddedLinesForProto() (map[string][]string, error) {
	cmd := exec.Command("git", "diff", "--unified=0", "HEAD~1", "HEAD")
	var out bytes.Buffer
	cmd.Stdout = &out

	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("git diff 실행 오류: %v", err)
	}

	lines := strings.Split(out.String(), "\n")
	addedLines := make(map[string][]string)
	var currentFile string

	for _, line := range lines {
		if strings.HasPrefix(line, "+++ b/") && strings.HasSuffix(line, ".proto") {
			currentFile = strings.TrimPrefix(line, "+++ b/")
		} else if currentFile != "" && strings.HasPrefix(line, "+") && !strings.HasPrefix(line, "+++") {
			addedLines[currentFile] = append(addedLines[currentFile], strings.TrimPrefix(line, "+"))
		}
	}

	return addedLines, nil
}

func parseProtoFromLastCommit() (map[string][][3]string, error) {
	addedLinesForProto, err := getLastCommitAddedLinesForProto()
	if err != nil {
		return nil, err
	}

	result := make(map[string][][3]string)
	for file, lines := range addedLinesForProto {
		fileBase := strings.TrimSuffix(file, ".proto")
		for _, line := range lines {
			if strings.HasPrefix(line, "rpc") {
				if functionName, argument, returnType, ok := parseRPCSignature(line); ok {
					result[fileBase] = append(result[fileBase], [3]string{functionName, argument, returnType})
				}
			}
		}
	}
	return result, nil
}

func main() {
	result, err := parseProtoFromLastCommit()
	if err != nil {
		fmt.Println("오류 발생:", err)
		return
	}

	for file, signatures := range result {
		fmt.Printf("\n--- %s ---\n", file)
		for _, sig := range signatures {
			fmt.Printf("rpc %s(%s) returns (%s)\n", sig[0], sig[1], sig[2])
		}
	}
}
