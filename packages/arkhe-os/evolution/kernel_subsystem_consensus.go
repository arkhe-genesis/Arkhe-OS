package evolution

import (
	"time"
)

// KernelSubsystemConsensusProtocol gerencia consenso interno entre subsistemas do kernel
type KernelSubsystemConsensusProtocol struct {
	kernelID           string
	votingTimeout      time.Duration
	consensusThreshold float64
	criticalThreshold  float64 // Threshold para aprovação de subsistemas críticos
}

// NewKernelSubsystemConsensusProtocol cria novo protocolo de consenso entre subsistemas
func NewKernelSubsystemConsensusProtocol(kernelID string) *KernelSubsystemConsensusProtocol {
	return &KernelSubsystemConsensusProtocol{
		kernelID:           kernelID,
		votingTimeout:      45 * time.Second,
		consensusThreshold: 0.67, // 2/3 para aprovação geral
		criticalThreshold:  0.80, // 4/5 para subsistemas críticos
	}
}

// ReachConsensus executa protocolo de consenso sobre proposta entre subsistemas
func (p *KernelSubsystemConsensusProtocol) ReachConsensus(
	proposal *KernelOptimizationProposal,
	subsystemStates []KernelSubsystemState,
) (*KernelConsensusResult, error) {
	if len(subsystemStates) < 2 {
		// Apenas um subsistema: auto-aprovação
		return &KernelConsensusResult{
			ProposalID:       proposal.ProposalID,
			Approved:         true,
			ApprovalRatio:    1.0,
			TotalVoters:      1,
			ApprovedVotes:    1,
			CriticalApproved: 1,
			CriticalTotal:    1,
			Timestamp:        time.Now(),
		}, nil
	}

	// Calcular pesos de voto baseados em criticidade e saúde
	votes := make(map[string]bool)
	weights := make(map[string]float64)
	criticalVotes := make(map[string]bool)
	criticalWeights := make(map[string]float64)

	for _, subsystem := range subsystemStates {
		// Peso = f(criticidade, saúde, centralidade)
		weight := 0.5*subsystem.Criticality +
			0.3*subsystem.HealthScore +
			0.2*subsystem.DependencyCentrality
		weights[subsystem.SubsystemID] = weight

		// Simular voto: subsistemas saudáveis e críticos tendem a ser conservadores
		vote := p.simulateSubsystemVote(proposal, subsystem, weight)
		votes[subsystem.SubsystemID] = vote

		// Separar votos de subsistemas críticos
		if subsystem.Criticality >= 0.8 {
			criticalVotes[subsystem.SubsystemID] = vote
			criticalWeights[subsystem.SubsystemID] = weight
		}
	}

	// Calcular resultado ponderado geral
	var totalWeight, approvedWeight float64
	var approvedCount, rejectedCount int
	for subsystemID, vote := range votes {
		w := weights[subsystemID]
		totalWeight += w
		if vote {
			approvedWeight += w
			approvedCount++
		} else {
			rejectedCount++
		}
	}

	approvalRatio := approvedWeight / totalWeight

	// Calcular resultado para subsistemas críticos
	var criticalTotalWeight, criticalApprovedWeight float64
	var criticalApprovedCount, criticalTotalCount int
	for subsystemID, vote := range criticalVotes {
		w := criticalWeights[subsystemID]
		criticalTotalWeight += w
		criticalTotalCount++
		if vote {
			criticalApprovedWeight += w
			criticalApprovedCount++
		}
	}

	criticalApprovalRatio := 0.0
	if criticalTotalWeight > 0 {
		criticalApprovalRatio = criticalApprovedWeight / criticalTotalWeight
	}

	// Decisão final: requer aprovação geral E aprovação de críticos (se houver)
	approved := approvalRatio >= p.consensusThreshold
	if criticalTotalCount > 0 {
		approved = approved && (criticalApprovalRatio >= p.criticalThreshold)
	}

	result := &KernelConsensusResult{
		ProposalID:       proposal.ProposalID,
		Approved:         approved,
		ApprovalRatio:    approvalRatio,
		TotalVoters:      len(votes),
		ApprovedVotes:    approvedCount,
		RejectedVotes:    rejectedCount,
		CriticalApproved: criticalApprovedCount,
		CriticalTotal:    criticalTotalCount,
		WeightedScore:    approvalRatio,
		Timestamp:        time.Now(),
	}

	return result, nil
}

// simulateSubsystemVote simula voto de um subsistema (em produção: avaliação real)
func (p *KernelSubsystemConsensusProtocol) simulateSubsystemVote(
	proposal *KernelOptimizationProposal,
	subsystem KernelSubsystemState,
	weight float64,
) bool {
	// Heurística: aprovar se benefício líquido > risco ajustado por criticidade
	netBenefit := proposal.ExpectedCoherenceGain*proposal.ExpectedSuccessProb -
		(0.5+0.3*subsystem.Criticality)*proposal.RiskScore

	// Subsistemas críticos são mais conservadores
	if subsystem.Criticality > 0.9 {
		netBenefit *= 0.85
	}

	// Subsistemas com baixa saúde podem rejeitar mudanças arriscadas
	if subsystem.HealthScore < 0.7 && proposal.RiskScore > 0.2 {
		return false
	}

	return netBenefit > 0.01
}
