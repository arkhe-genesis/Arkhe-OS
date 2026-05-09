// cli/commands/game.go
package commands

import (
	"github.com/spf13/cobra"
)

var GameCmd = &cobra.Command{
	Use:   "game",
	Short: "Arkhe.D game artifacts parser and coherence analyzer",
	Long:  "Commands for parsing game development artifacts like Unity prefabs/scenes and Steam manifests.",
}

func init() {
	GameCmd.AddCommand(gameParseCmd)
}
