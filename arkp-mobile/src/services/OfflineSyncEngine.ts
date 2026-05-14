// ============================================================================
// OfflineSyncEngine — Sincronização adaptativa para ambientes com conectividade limitada
// ============================================================================

import { ReviewTask, ReviewVote, ConsensusResult, ReviewerMetrics } from '../types/arkhe';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { NetworkQuality } from '../utils/NetworkQuality';

export class OfflineSyncEngine {
  private static readonly STORAGE_KEYS = {
    PENDING_TASKS: 'arkhe:pending_tasks',
    SUBMITTED_VOTES: 'arkhe:submitted_votes',
    PLUGIN_CACHE: 'arkhe:plugin_cache',
    METRICS_CACHE: 'arkhe:metrics_cache',
    LAST_SYNC: 'arkhe:last_sync',
  };

  private static readonly SYNC_PRIORITIES: Record<string, number> = {
    votes: 1,      // Mais importante: votos do revisor
    tasks: 2,      // Tarefas pendentes
    plugins: 3,    // Plugins instalados
    metrics: 4,    // Métricas de reputação
  };

  /**
   * Sincroniza todos os dados pendentes com o servidor
   * Adapta estratégia baseada na qualidade da rede
   */
  static async syncAll(
    reviewerId: string,
    authToken: string,
    isOffline: boolean
  ): Promise<void> {
    const networkQuality = await NetworkQuality.assess();

    // Estratégia de sincronização baseada na qualidade da rede
    const strategy = this.determineSyncStrategy(networkQuality, isOffline);

    // Sincronizar por prioridade
    for (const priority of Object.keys(this.SYNC_PRIORITIES).sort(
      (a, b) => this.SYNC_PRIORITIES[a] - this.SYNC_PRIORITIES[b]
    )) {
      if (strategy[priority]) {
        await this.syncByPriority(priority, reviewerId, authToken, strategy);
      }
    }

    // Atualizar timestamp de última sincronização
    await AsyncStorage.setItem(
      this.STORAGE_KEYS.LAST_SYNC,
      Date.now().toString()
    );
  }

  /**
   * Determina estratégia de sincronização baseada na qualidade da rede
   */
  private static determineSyncStrategy(
    networkQuality: 'excellent' | 'good' | 'poor' | 'none',
    isOffline: boolean
  ): Record<string, boolean> {
    if (isOffline || networkQuality === 'none') {
      // Modo offline: apenas armazenar localmente
      return { votes: true, tasks: true, plugins: false, metrics: false };
    }

    if (networkQuality === 'poor') {
      // Banda limitada: priorizar votos e tarefas
      return { votes: true, tasks: true, plugins: false, metrics: false };
    }

    if (networkQuality === 'good') {
      // Banda moderada: sincronizar tudo exceto plugins grandes
      return { votes: true, tasks: true, plugins: true, metrics: true };
    }

    // Excelente: sincronização completa com prefetch
    return { votes: true, tasks: true, plugins: true, metrics: true };
  }

  /**
   * Sincroniza dados por categoria de prioridade
   */
  private static async syncByPriority(
    priority: string,
    reviewerId: string,
    authToken: string,
    strategy: Record<string, boolean>
  ): Promise<void> {
    switch (priority) {
      case 'votes':
        await this.syncVotes(reviewerId, authToken);
        break;
      case 'tasks':
        await this.syncTasks(reviewerId, authToken);
        break;
      case 'plugins':
        if (strategy.plugins) {
          await this.syncPlugins(reviewerId, authToken);
        }
        break;
      case 'metrics':
        if (strategy.metrics) {
          await this.syncMetrics(reviewerId, authToken);
        }
        break;
    }
  }

  /**
   * Sincroniza votos submetidos offline
   */
  private static async syncVotes(reviewerId: string, authToken: string): Promise<void> {
    const pendingVotes = await AsyncStorage.getItem(
      this.STORAGE_KEYS.SUBMITTED_VOTES
    );

    if (!pendingVotes) return;

    const votes: Array<{
      taskId: string;
      vote: ReviewVote;
      rationale: string;
      confidence: number;
      timestamp: number;
    }> = JSON.parse(pendingVotes);

    // Enviar votos pendentes
    for (const vote of votes) {
      try {
        await fetch(`/api/v1/review/${vote.taskId}/vote`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
          },
          body: JSON.stringify({
            vote: vote.vote,
            rationale: vote.rationale,
            confidence: vote.confidence,
          }),
        });

        // Remover voto enviado da fila pendente
        const remaining = votes.filter(v =>
          !(v.taskId === vote.taskId && v.timestamp === vote.timestamp)
        );
        await AsyncStorage.setItem(
          this.STORAGE_KEYS.SUBMITTED_VOTES,
          JSON.stringify(remaining)
        );
      } catch (error) {
        console.warn(`Failed to sync vote for task ${vote.taskId}:`, error);
        // Manter na fila para próxima tentativa
      }
    }
  }

  /**
   * Sincroniza tarefas pendentes do servidor
   */
  private static async syncTasks(reviewerId: string, authToken: string): Promise<void> {
    try {
      const response = await fetch('/api/v1/review/pending', {
        headers: { 'Authorization': `Bearer ${authToken}` },
      });

      if (!response.ok) throw new Error('Failed to fetch tasks');

      const tasks: ReviewTask[] = await response.json();

      // Armazenar localmente para acesso offline
      await AsyncStorage.setItem(
        this.STORAGE_KEYS.PENDING_TASKS,
        JSON.stringify(tasks)
      );
    } catch (error) {
      console.warn('Failed to sync tasks:', error);
      // Usar cache local se disponível
    }
  }

  private static async syncPlugins(reviewerId: string, authToken: string): Promise<void> {
    // Stub
  }

  private static async syncMetrics(reviewerId: string, authToken: string): Promise<void> {
    // Stub
  }

  /**
   * Obtém tarefas pendentes do cache local
   */
  static async getPendingTasks(reviewerId: string): Promise<ReviewTask[]> {
    const cached = await AsyncStorage.getItem(
      this.STORAGE_KEYS.PENDING_TASKS
    );

    if (!cached) return [];

    const tasks: ReviewTask[] = JSON.parse(cached);

    // Filtrar tarefas atribuídas ao revisor
    return tasks.filter(task =>
      task.assigned_reviewers.includes(reviewerId)
    );
  }

  /**
   * Armazena voto submetido offline para sincronização posterior
   */
  static async queueVote(
    taskId: string,
    vote: ReviewVote,
    rationale: string,
    confidence: number
  ): Promise<void> {
    const pendingVotes = await AsyncStorage.getItem(
      this.STORAGE_KEYS.SUBMITTED_VOTES
    );

    const votes = pendingVotes ? JSON.parse(pendingVotes) : [];

    votes.push({
      taskId,
      vote,
      rationale,
      confidence,
      timestamp: Date.now(),
    });

    await AsyncStorage.setItem(
      this.STORAGE_KEYS.SUBMITTED_VOTES,
      JSON.stringify(votes)
    );
  }

  /**
   * Obtém métricas do revisor (cache local ou servidor)
   */
  static async getReviewerMetrics(reviewerId: string): Promise<ReviewerMetrics | null> {
    // Tentar cache primeiro
    const cached = await AsyncStorage.getItem(
      this.STORAGE_KEYS.METRICS_CACHE
    );

    if (cached) {
      const metrics: Record<string, ReviewerMetrics> = JSON.parse(cached);
      if (metrics[reviewerId]) {
        return metrics[reviewerId];
      }
    }

    // Se não houver cache, tentar servidor
    try {
      const response = await fetch(`/api/v1/reputation/${reviewerId}`);
      if (!response.ok) throw new Error('Failed to fetch metrics');

      const metrics = await response.json();

      // Atualizar cache
      const allMetrics = cached ? JSON.parse(cached) : {};
      allMetrics[reviewerId] = metrics;
      await AsyncStorage.setItem(
        this.STORAGE_KEYS.METRICS_CACHE,
        JSON.stringify(allMetrics)
      );

      return metrics;
    } catch (error) {
      console.warn('Failed to fetch metrics:', error);
      return null;
    }
  }
}
