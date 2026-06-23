package cmd

import (
	"fmt"
	"logq/internal/parser"
	"github.com/spf13/cobra"
	"github.com/hpcloud/tail"
	"github.com/bytedance/sonic"
)

var tailCmd = &cobra.Command{
	Use:   "tail [file]",
	Short: "Tail a log file and print formatted entries",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		filepath := args[0]
		t, err := tail.TailFile(filepath, tail.Config{Follow: true})
		if err != nil {
			fmt.Printf("Error tailing file: %v\n", err)
			return
		}

		for line := range t.Lines {
			var entry map[string]interface{}
			if err := sonic.Unmarshal([]byte(line.Text), &entry); err != nil {
				continue
			}

			// Format for quick view: Time | User | Model | Cost
			createdAt := parser.GetValue(entry, "created_at")
			userID := parser.GetValue(entry, "user_id")
			model := parser.GetValue(entry, "model")
			cost := parser.GetValue(entry, "total_cost")

			fmt.Printf("%v | %-10v | %-20v | $%v\n", createdAt, userID, model, cost)
		}
	},
}

func init() {
	rootCmd.AddCommand(tailCmd)
}
