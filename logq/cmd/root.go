package cmd

import (
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "logq",
	Short: "logq is a blindingly fast AI log analyzer",
	Long:  `logq is specifically built for analyzing high-throughput LLM gateway traffic from .jsonl files.`,
}

func Execute() error {
	return rootCmd.Execute()
}

func init() {
	// Root flags if needed
}
