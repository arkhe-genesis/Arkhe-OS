package commands

import (
	"fmt"
	"io/ioutil"
	"log"
	"encoding/json"

	"github.com/spf13/cobra"

	"arkhe/parser/frontends/ui/formats"
	"arkhe/parser/frontends/ui/models"
)

var UiParseCmd = &cobra.Command{
	Use:   "ui-parse [filepath]",
	Short: "Parse CSS and calculate UI coherence",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		filepath := args[0]

		source, err := ioutil.ReadFile(filepath)
		if err != nil {
			log.Fatalf("Error reading file: %v", err)
		}

		spec, err := formats.ParseCSS(source)
		if err != nil {
			log.Fatalf("Error parsing CSS: %v", err)
		}

		graph := models.MapUISpecToLFIR(spec)

		output, err := json.MarshalIndent(graph, "", "  ")
		if err != nil {
			log.Fatalf("Error marshalling graph: %v", err)
		}

		fmt.Println(string(output))
	},
}
