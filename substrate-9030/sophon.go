package main

import (
    "fmt"
    "os"
    "github.com/arkhe-os/sophon"
)

func main() {
    agent := sophon.NewAgent("sophon-001")
    if err := agent.Start(); err != nil {
        fmt.Fprintf(os.Stderr, "Sophon failed to start: %v\n", err)
        os.Exit(1)
    }
    fmt.Println("Sophon agent running on ARKHE mesh")
}
