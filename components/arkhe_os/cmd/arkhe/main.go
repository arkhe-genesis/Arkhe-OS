// cmd/arkhe/main.go
package main

import (
	"fmt"
	"os"

	"arkhe_os/cli/commands"
	"github.com/spf13/cobra"
)

func main() {
	rootCmd := &cobra.Command{
		Use:   "arkhe",
		Short: "Arkhe OS CLI",
	}

	rootCmd.AddCommand(commands.GameCmd)

	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
