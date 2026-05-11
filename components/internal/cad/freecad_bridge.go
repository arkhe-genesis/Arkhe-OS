package cad

import (
	"context"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"time"
)

// FreeCADBridge manages the interaction with the headless FreeCAD container
type FreeCADBridge struct {
	DockerImage string
	WorkDir     string
}

// NewFreeCADBridge creates a new instance of the bridge
func NewFreeCADBridge(workDir string) *FreeCADBridge {
	return &FreeCADBridge{
		DockerImage: "arkhe-freecad-headless:latest", // Assumes the image is built
		WorkDir:     workDir,
	}
}

// ConvertCADToVoxel6D runs the headless FreeCAD pipeline via Docker
func (b *FreeCADBridge) ConvertCADToVoxel6D(ctx context.Context, inputFilename string, resolution float64, targetPhase float64) (string, error) {
	// Ensure input file exists
	inputPath := filepath.Join(b.WorkDir, inputFilename)
	if _, err := os.Stat(inputPath); os.IsNotExist(err) {
		return "", fmt.Errorf("input file not found: %s", inputPath)
	}

	// Generate output filename
	outputFilename := fmt.Sprintf("%s.v6d", inputFilename)
	outputPath := filepath.Join(b.WorkDir, outputFilename)

	// Build the Docker command
	// We mount the WorkDir to /data inside the container
	cmdArgs := []string{
		"run", "--rm",
		"-v", fmt.Sprintf("%s:/data", b.WorkDir),
		b.DockerImage,
		"python3", "/app/headless_pipeline.py",
		fmt.Sprintf("/data/%s", inputFilename),
		fmt.Sprintf("/data/%s", outputFilename),
		"--res", fmt.Sprintf("%f", resolution),
		"--phase", fmt.Sprintf("%f", targetPhase),
	}

	log.Printf("Running FreeCAD conversion: docker %v", cmdArgs)

	cmd := exec.CommandContext(ctx, "docker", cmdArgs...)

	// Capture output for debugging
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("FreeCAD conversion failed: %w\nOutput: %s", err, string(output))
	}

	log.Printf("Conversion successful. Output: %s", string(output))

	// Verify the output file was created
	if _, err := os.Stat(outputPath); os.IsNotExist(err) {
		return "", fmt.Errorf("output file was not created: %s", outputPath)
	}

	return outputPath, nil
}
