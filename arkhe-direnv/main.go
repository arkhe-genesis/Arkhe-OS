package main

import (
	"arkhe-direnv/internal/env"
	"arkhe-direnv/internal/git"
	"arkhe-direnv/internal/opcodes"
	"arkhe-direnv/internal/parser"
	"crypto/sha256"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "arkhe-direnv",
	Short: "Arkhe(n) Phase Environment Loader",
}

func getAllowFile() string {
	home, _ := os.UserHomeDir()
	path := filepath.Join(home, ".config", "arkhe", "direnv_allow")
	os.MkdirAll(filepath.Dir(path), 0755)
	return path
}

func getFileHash(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()
	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", err
	}
	return fmt.Sprintf("%x", h.Sum(nil)), nil
}

func isAllowed(path string) bool {
	absPath, _ := filepath.Abs(path)
	hash, err := getFileHash(absPath)
	if err != nil {
		return false
	}

	data, err := os.ReadFile(getAllowFile())
	if err != nil {
		return false
	}

	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		if strings.TrimSpace(line) == absPath+":"+hash {
			return true
		}
	}
	return false
}

var exportCmd = &cobra.Command{
	Use:   "export",
	Short: "Evaluate .arkhenv and output shell exports",
	Run: func(cmd *cobra.Command, args []string) {
		state := env.NewPhaseState()

		arkhEnvPath := findArkhenv()
		if arkhEnvPath == "" {
			fmt.Print(state.Relax())
			return
		}

		if !isAllowed(arkhEnvPath) {
			fmt.Fprintf(os.Stderr, "arkhe-direnv: %s is not allowed. Run 'arkhe-direnv allow' to authorize it.\n", arkhEnvPath)
			fmt.Print(state.Relax())
			return
		}

		f, err := os.Open(arkhEnvPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			return
		}
		defer f.Close()

		prog, err := parser.Parse(f)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Parse Error: %v\n", err)
			return
		}

		interp := opcodes.NewInterpreter(state)
		if err := interp.Execute(prog); err != nil {
			fmt.Fprintf(os.Stderr, "Execution Error: %v\n", err)
			return
		}

		_ = git.ApplyGitPhase(state)
		fmt.Print(state.Export())
	},
}

var allowCmd = &cobra.Command{
	Use:   "allow [path]",
	Short: "Authorize the current directory's .arkhenv",
	Run: func(cmd *cobra.Command, args []string) {
		path := ".arkhenv"
		if len(args) > 0 {
			path = args[0]
		}

		absPath, _ := filepath.Abs(path)
		hash, err := getFileHash(absPath)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			return
		}

		entry := absPath + ":" + hash

		// Simple append for now
		f, err := os.OpenFile(getAllowFile(), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error: %v\n", err)
			return
		}
		defer f.Close()
		fmt.Fprintln(f, entry)

		fmt.Printf("arkhe-direnv: %s allowed and signed.\n", absPath)
	},
}

var hookCmd = &cobra.Command{
	Use:   "hook [shell]",
	Short: "Output the shell hook script",
	Args:  cobra.ExactArgs(1),
	Run: func(cmd *cobra.Command, args []string) {
		shell := args[0]
		switch shell {
		case "bash":
			fmt.Println(`arkhe_direnv_hook() {
    local previous_exit_status=$?
    trap -- '' SIGINT
    eval "$(arkhe-direnv export)"
    trap - SIGINT
    return $previous_exit_status
}
if [[ ";${PROMPT_COMMAND:-};" != *";arkhe_direnv_hook;"* ]]; then
    PROMPT_COMMAND="arkhe_direnv_hook${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
fi`)
		case "zsh":
			fmt.Println(`_arkhe_direnv_hook() {
    trap -- '' SIGINT
    eval "$(arkhe-direnv export)"
    trap - SIGINT
}
typeset -ag precmd_functions
if (( ! ${precmd_functions[(I)_arkhe_direnv_hook]} )); then
    precmd_functions=(_arkhe_direnv_hook $precmd_functions)
fi`)
		default:
			fmt.Fprintf(os.Stderr, "Unsupported shell: %s\n", shell)
		}
	},
}

func findArkhenv() string {
	files := []string{".arkhenv", ".phaseenv"}
	for _, f := range files {
		if _, err := os.Stat(f); err == nil {
			return f
		}
	}
	return ""
}

func init() {
	rootCmd.AddCommand(exportCmd)
	rootCmd.AddCommand(allowCmd)
	rootCmd.AddCommand(hookCmd)
}

func main() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
}
