package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	"arkhe_os/parser/frontends"
)

func main() {
	var targetDir string
	flag.StringVar(&targetDir, "dir", ".", "Directory to parse")
	flag.Parse()

	gooseFrontend := frontends.NewGooseFrontend()

	count := 0
	err := filepath.Walk(targetDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() {
			base := filepath.Base(path)
			if base == ".goosehints" || base == "AGENTS.md" {
				content, err := os.ReadFile(path)
				if err != nil {
					return err
				}

				graph, err := gooseFrontend.Parse(string(content))
				if err != nil {
					return err
				}

				fmt.Printf("Parsed %s: %d nodes, parse time: %.2f ms\n", path, len(graph.Nodes), graph.Metrics.ParseTimeMs)
				count++
			}
		}

		return nil
	})

	if err != nil {
		fmt.Printf("Error walking %s: %v\n", targetDir, err)
	}

	fmt.Printf("Total files parsed with GooseFrontend: %d\n", count)
	fmt.Println("Integration of Goose into Arkhe's Corvo via PolymathParser complete.")
}
