// web3/game_asset_tokenizer.go
// Bridge para tokenização de achievements e ativos de jogos como Φ‑tokens
package web3

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"time"

	"arkhe_os/web3/octra"
)

// GameAssetToken represents a tokenized game achievement or asset
type GameAssetToken struct {
	TokenID         string    `json:"token_id"`
	GameAppID       string    `json:"game_app_id"`
	AssetType       string    `json:"asset_type"` // "achievement", "item", "scene"
	AssetID         string    `json:"asset_id"`
	CoherenceScore  float64   `json:"coherence_score"`
	MetadataHash    string    `json:"metadata_hash"`
	MintedAt        time.Time `json:"minted_at"`
	OwnerNPub       string    `json:"owner_npub"`
}

// TokenizeAchievement converte um achievement Steam em Φ‑token
func TokenizeAchievement(
	appID, achievementID string,
	coherenceScore float64,
	ownerNPub string,
) (*GameAssetToken, error) {
	// Gerar ID único baseado em hash dos metadados
	metadata := fmt.Sprintf("%s:%s:%.3f", appID, achievementID, coherenceScore)
	hash := sha256.Sum256([]byte(metadata))
	tokenID := hex.EncodeToString(hash[:8])

	token := &GameAssetToken{
		TokenID:        fmt.Sprintf("achievement_%s", tokenID),
		GameAppID:      appID,
		AssetType:      "achievement",
		AssetID:        achievementID,
		CoherenceScore: coherenceScore,
		MetadataHash:   hex.EncodeToString(hash[:]),
		MintedAt:       time.Now(),
		OwnerNPub:      ownerNPub,
	}

	return token, nil
}

// RegisterTokenOnChain registra o token no ledger Octra
func RegisterTokenOnChain(token *GameAssetToken, octraClient *octra.Client) error {
	payload := map[string]interface{}{
		"token_id":         token.TokenID,
		"asset_type":       token.AssetType,
		"coherence_score":  token.CoherenceScore,
		"metadata_hash":    token.MetadataHash,
		"owner_npub":       token.OwnerNPub,
		"mint_timestamp":   token.MintedAt.Unix(),
	}

	// Submeter para ledger
	entry, err := octraClient.SubmitValidation(
		fmt.Sprintf("game_asset_%s", token.TokenID),
		payload,
		nil, // ZK proof opcional
	)
	if err != nil {
		return fmt.Errorf("failed to register token: %w", err)
	}

	// Atualizar token com info do ledger
	token.MetadataHash = entry.LedgerTX[:16]
	return nil
}

// CalculatePhiReward calcula recompensa Φ baseada na coerência do ativo
func CalculatePhiReward(coherenceScore float64) float64 {
	// Recompensa base: coerência × 10 Φ
	// Bônus para alta coerência (>0.9)
	baseReward := coherenceScore * 10.0
	if coherenceScore > 0.9 {
		baseReward *= 1.5 // 50% bônus
	}
	return baseReward
}
