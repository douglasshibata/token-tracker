package processor

import (
	"bufio"
	"os"
	"github.com/bytedance/sonic"
)

type LogEntry map[string]interface{}

func ProcessFile(filepath string, handler func(LogEntry) error) error {
	file, err := os.Open(filepath)
	if err != nil {
		return err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	// Buffer size for large log lines (default is 64k, AI logs can be huge)
	buf := make([]byte, 0, 1024*1024)
	scanner.Buffer(buf, 5*1024*1024)

	for scanner.Scan() {
		var entry LogEntry
		if err := sonic.Unmarshal(scanner.Bytes(), &entry); err != nil {
			// Skip malformed lines or log them? For now, skip.
			continue
		}
		if err := handler(entry); err != nil {
			return err
		}
	}

	return scanner.Err()
}
