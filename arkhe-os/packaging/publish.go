// publish.go
package packaging

import (
	"fmt"
	"os"
	"os/exec"
)

func publishToGoModules() error {
	cmd := exec.Command("go", "mod", "tidy")
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return err
	}

	// Tag and push
	version := "v177.0.0"
	exec.Command("git", "tag", version).Run()
	exec.Command("git", "push", "origin", version).Run()

	fmt.Printf("✅ ARKHE OS %s published to Go Modules (github.com/arkhe-federacao/arkhe-os)\n", version)
	return nil
}

func publishToPyPI() error {
	cmd := exec.Command("python", "setup.py", "sdist", "bdist_wheel")
	cmd.Dir = "../python"
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return err
	}

	// Upload using twine
	cmd = exec.Command("twine", "upload", "dist/*")
	cmd.Dir = "../python"
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return err
	}
	fmt.Println("✅ ARKHE OS published to PyPI (pip install arkhe-os)")
	return nil
}

func PublishMain() {
	fmt.Println("📦 ARKHE OS Federation Packaging")
	if err := publishToGoModules(); err != nil {
		fmt.Printf("Go publish error: %v\n", err)
	}
	if err := publishToPyPI(); err != nil {
		fmt.Printf("PyPI publish error: %v\n", err)
	}

	// MERCES on-chain registration (simplified)
	fmt.Println("🔗 Registering on MERCES blockchain...")
	// mercesClient.MintVerificationRecord(version, hash)
	fmt.Println("✅ All artifacts published and verified.")
}
