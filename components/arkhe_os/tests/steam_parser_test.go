// tests/steam_parser_test.go
package tests

import (
	"testing"

	"arkhe_os/parser/frontends"
	"github.com/stretchr/testify/assert"
)

func TestSteamVDFParser_Parse(t *testing.T) {
	parser := frontends.NewSteamVDFParser()

	vdfContent := `"AppState"
{
	"appid"		"123456"
	"Universe"		"1"
	"name"		"Test Game"
	"StateFlags"		"4"
	"installdir"		"TestGame"
	"LastUpdated"		"1600000000"
	"SizeOnDisk"		"1000000"
	"StagingSize"		"0"
	"buildid"		"555555"
	"LastOwner"		"76561198000000000"
	"UpdateResult"		"0"
	"BytesToDownload"		"0"
	"BytesDownloaded"		"0"
	"BytesToStage"		"0"
	"BytesStaged"		"0"
	"TargetBuildID"		"0"
	"AutoUpdateBehavior"		"0"
	"AllowOtherDownloadsWhileRunning"		"0"
	"ScheduledAutoUpdate"		"0"
	"InstalledDepots"
	{
		"123457"
		{
			"manifest"		"1111111111111111111"
			"size"		"1000000"
		}
	}
}`

	graph, err := parser.Parse([]byte(vdfContent), "appmanifest_123456.acf", nil)
	assert.NoError(t, err)
	assert.NotNil(t, graph)
}
