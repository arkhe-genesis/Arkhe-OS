package arkhe

// Dummy integration to verify integration logic
func StartDemo() {
	_ = NewLanguageCatalog()
	_ = NewTreeSitterFrontend("python")
	_ = NewLanguageDetector(NewLanguageCatalog())
}
