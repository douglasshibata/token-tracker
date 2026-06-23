package cmd

import (
	"fmt"
	"os"
	"logq/internal/processor"
	"logq/internal/parser"
	"github.com/spf13/cobra"
	"github.com/olekukonko/tablewriter"
)

var (
	groupBy string
	sumField string
)

var aggregateCmd = &cobra.Command{
	Use:   "aggregate [file]",
	Short: "Aggregate log entries",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		filepath := args[0]

		aggregates := make(map[string]float64)
		counts := make(map[string]int)

		err := processor.ProcessFile(filepath, func(entry processor.LogEntry) error {
			groupVal := fmt.Sprintf("%v", parser.GetValue(entry, groupBy))
			counts[groupVal]++

			if sumField != "" {
				val := parser.GetValue(entry, sumField)
				if f, ok := toFloat(val); ok {
					aggregates[groupVal] += f
				}
			}
			return nil
		})

		if err != nil {
			fmt.Printf("Error processing file: %v\n", err)
			return
		}

		table := tablewriter.NewWriter(os.Stdout)
		header := []string{groupBy, "Count"}
		if sumField != "" {
			header = append(header, "Sum of "+sumField)
		}
		table.Header(header)

		for group, count := range counts {
			row := []string{group, fmt.Sprintf("%d", count)}
			if sumField != "" {
				row = append(row, fmt.Sprintf("%.4f", aggregates[group]))
			}
			table.Append(row)
		}

		table.Render()
	},
}

func toFloat(val interface{}) (float64, bool) {
	switch v := val.(type) {
	case float64:
		return v, true
	case int:
		return float64(v), true
	case int64:
		return float64(v), true
	case string:
		var f float64
		_, err := fmt.Sscanf(v, "%f", &f)
		return f, err == nil
	}
	return 0, false
}

func init() {
	aggregateCmd.Flags().StringVarP(&groupBy, "group-by", "g", "", "Field to group by (e.g. model)")
	aggregateCmd.Flags().StringVarP(&sumField, "sum", "", "", "Field to sum (e.g. total_cost)")
	aggregateCmd.MarkFlagRequired("group-by")
	rootCmd.AddCommand(aggregateCmd)
}
