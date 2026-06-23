package cmd

import (
	"fmt"
	"os"
	"strings"
	"logq/internal/processor"
	"logq/internal/parser"
	"github.com/spf13/cobra"
	"github.com/olekukonko/tablewriter"
)

var (
	filter   string
	sortBy   string
	limit    int
	columns  string
)

var searchCmd = &cobra.Command{
	Use:   "search [file]",
	Short: "Search for specific log entries",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		filepath := args[0]
		cols := strings.Split(columns, ",")
		table := tablewriter.NewWriter(os.Stdout)

		// tablewriter v1.1.4 uses Header() and Append() returns error
		table.Header(cols)

		count := 0
		err := processor.ProcessFile(filepath, func(entry processor.LogEntry) error {
			if limit > 0 && count >= limit {
				return nil
			}

			// Apply filter (simple equality for MVP)
			if filter != "" {
				parts := strings.Split(filter, "=")
				if len(parts) == 2 {
					val := parser.GetValue(entry, parts[0])
					if fmt.Sprintf("%v", val) != parts[1] {
						return nil
					}
				}
			}

			row := make([]string, len(cols))
			for i, col := range cols {
				val := parser.GetValue(entry, col)
				row[i] = redactPII(fmt.Sprintf("%v", val))
			}
			table.Append(row)
			count++
			return nil
		})

		if err != nil {
			fmt.Printf("Error processing file: %v\n", err)
			return
		}

		table.Render()
	},
}

func redactPII(val string) string {
	if strings.HasPrefix(val, "sk-") {
		return val[:7] + "****"
	}
	// Add more patterns...
	return val
}

func init() {
	searchCmd.Flags().StringVarP(&filter, "filter", "f", "", "Filter entries (e.g. status=error)")
	searchCmd.Flags().StringVarP(&sortBy, "sort-by", "s", "", "Sort by field")
	searchCmd.Flags().IntVarP(&limit, "limit", "l", 0, "Limit results")
	searchCmd.Flags().StringVarP(&columns, "columns", "c", "created_at,user_id,model,total_cost", "Columns to display")
	rootCmd.AddCommand(searchCmd)
}
