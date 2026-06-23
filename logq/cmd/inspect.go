package cmd

import (
	"fmt"
	"logq/internal/processor"
	"logq/internal/parser"
	"github.com/spf13/cobra"
	"github.com/bytedance/sonic"
)

var (
	inspectID string
)

var inspectCmd = &cobra.Command{
	Use:   "inspect [file]",
	Short: "Inspect a single log entry by ID",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		filepath := args[0]
		found := false

		err := processor.ProcessFile(filepath, func(entry processor.LogEntry) error {
			if found {
				return nil
			}

			id := parser.GetValue(entry, "id")
			if id == nil {
				// Try common ID fields
				id = parser.GetValue(entry, "request_id")
			}

			if fmt.Sprintf("%v", id) == inspectID {
				pretty, _ := sonic.ConfigDefault.MarshalIndent(entry, "", "  ")
				fmt.Println(string(pretty))
				found = true
			}
			return nil
		})

		if err != nil {
			fmt.Printf("Error processing file: %v\n", err)
			return
		}

		if !found {
			fmt.Printf("Request with ID %s not found\n", inspectID)
		}
	},
}

func init() {
	inspectCmd.Flags().StringVar(&inspectID, "id", "", "ID of the request to inspect")
	inspectCmd.MarkFlagRequired("id")
	rootCmd.AddCommand(inspectCmd)
}
