import { PluginDetailScreen } from "./components/PluginDetailScreen";
import { ReviewDetailScreen } from "./components/ReviewDetailScreen";
import { SettingsScreen } from "./components/SettingsScreen";
import { ProfileScreen } from "./components/ProfileScreen";
import { Icon } from "./components/Icon";
import { ArkheAuth } from "./utils/ArkheAuth";
// ============================================================================
// ARKHE FIELD — Mobile App para Revisores em Missão
// Substrato 9004: Acesso offline-first com sincronização adaptativa
// ============================================================================

import React, { useState, useEffect, useCallback, createContext, useContext } from 'react';
import {
  NavigationContainer,
} from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import {
  View, Text, StyleSheet, TouchableOpacity,
  ScrollView, RefreshControl, Alert, ActivityIndicator, TextInput
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import { useTranslation } from 'react-i18next';
import {
  ReviewTask, ReviewVote, ConsensusResult,
  ReviewerMetrics, PluginListing
} from '../types/arkhe';
import { OfflineSyncEngine } from './services/OfflineSyncEngine';
import { NotificationService } from './services/NotificationService';
import { BiometricAuth } from './components/BiometricAuth';
import { TaskCard } from './components/TaskCard';
import { ReputationBadge } from './components/ReputationBadge';
import { PluginBrowser } from './components/PluginBrowser';
import { LanguageSelector } from './components/LanguageSelector';

// ============================================================================
// CONTEXTOS GLOBAIS
// ============================================================================

interface ArkheContextType {
  reviewerId: string | null;
  authToken: string | null;
  isOffline: boolean;
  syncStatus: 'idle' | 'syncing' | 'error';
  setReviewerId: (id: string | null) => void;
  setAuthToken: (token: string | null) => void;
  triggerSync: () => Promise<void>;
}

export const ArkheContext = createContext<ArkheContextType>({
  reviewerId: null,
  authToken: null,
  isOffline: false,
  syncStatus: 'idle',
  setReviewerId: () => {},
  setAuthToken: () => {},
  triggerSync: async () => {},
});

// ============================================================================
// NAVEGAÇÃO PRINCIPAL
// ============================================================================

const Stack = createNativeStackNavigator();
const Tabs = createBottomTabNavigator();

// Tela de Login
const LoginScreen: React.FC<{ onLogin: (token: string) => void }> = ({ onLogin }) => {
  const { t } = useTranslation();
  const [orcid, setOrcid] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!orcid.match(/^0000-000\d-\d{4}(-\d{3}[X\d])?$/)) {
      Alert.alert(t('error'), t('invalid_orcid'));
      return;
    }

    setLoading(true);
    try {
      // Autenticação via ORCID OAuth
      const token = await ArkheAuth.loginWithORCID(orcid);
      await AsyncStorage.setItem('auth_token', token);
      await AsyncStorage.setItem('reviewer_id', orcid);
      onLogin(token);
    } catch (error: any) {
      Alert.alert(t('error'), error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.loginContainer}>
      <Text style={styles.logo}>🏛️ ARKHE FIELD</Text>
      <Text style={styles.subtitle}>{t('reviewer_login')}</Text>

      <View style={styles.inputContainer}>
        <Text style={styles.label}>{t('orcid_id')}</Text>
        <TextInput
          style={styles.input}
          value={orcid}
          onChangeText={setOrcid}
          placeholder="0000-0000-0000-0000"
          keyboardType="default"
          autoCapitalize="none"
        />
      </View>

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={handleLogin}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>{t('login')}</Text>
        )}
      </TouchableOpacity>

      <LanguageSelector />

      <BiometricAuth onAuthSuccess={handleLogin} />
    </View>
  );
};

// Dashboard Principal
const DashboardScreen: React.FC<{ navigation: any }> = ({ navigation }) => {
  const { t } = useTranslation();
  const { reviewerId, isOffline, syncStatus, triggerSync } = useContext(ArkheContext);
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [metrics, setMetrics] = useState<ReviewerMetrics | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadDashboard = useCallback(async () => {
    try {
      const [tasksData, metricsData] = await Promise.all([
        OfflineSyncEngine.getPendingTasks(reviewerId!),
        OfflineSyncEngine.getReviewerMetrics(reviewerId!)
      ]);
      setTasks(tasksData);
      setMetrics(metricsData);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    }
  }, [reviewerId]);

  const onRefresh = async () => {
    setRefreshing(true);
    await triggerSync();
    await loadDashboard();
    setRefreshing(false);
  };

  useEffect(() => {
    loadDashboard();
    // Auto-refresh a cada 15 minutos
    const interval = setInterval(loadDashboard, 15 * 60 * 1000);
    return () => clearInterval(interval);
  }, [loadDashboard]);

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {/* Header com status */}
      <View style={styles.header}>
        <View>
          <Text style={styles.greeting}>{t('welcome')}, {metrics?.name || reviewerId}</Text>
          <ReputationBadge tier={metrics?.reputation_tier} score={metrics?.reputation_score} />
        </View>
        <View style={styles.statusBadges}>
          {isOffline && (
            <View style={[styles.badge, styles.offlineBadge]}>
              <Text style={styles.badgeText}>📴 {t('offline')}</Text>
            </View>
          )}
          {syncStatus === 'syncing' && (
            <View style={[styles.badge, styles.syncingBadge]}>
              <ActivityIndicator size="small" color="#fff" />
              <Text style={styles.badgeText}>{t('syncing')}</Text>
            </View>
          )}
        </View>
      </View>

      {/* Estatísticas rápidas */}
      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{tasks.filter(t => t.status === 'pending').length}</Text>
          <Text style={styles.statLabel}>{t('pending_tasks')}</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{metrics?.total_reviews || 0}</Text>
          <Text style={styles.statLabel}>{t('total_reviews')}</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statNumber}>{metrics?.qip_earned?.toFixed(1) || '0.0'}</Text>
          <Text style={styles.statLabel}>QIP</Text>
        </View>
      </View>

      {/* Lista de tarefas pendentes */}
      <Text style={styles.sectionTitle}>{t('pending_reviews')}</Text>
      {tasks.filter(t => t.status === 'pending').map(task => (
        <TaskCard
          key={task.task_id}
          task={task}
          onPress={() => navigation.navigate('ReviewDetail', { taskId: task.task_id })}
        />
      ))}

      {/* Plugins instalados */}
      <Text style={styles.sectionTitle}>{t('active_plugins')}</Text>
      <PluginBrowser mode="installed" />

      {/* Botão de sincronização manual */}
      {isOffline && (
        <TouchableOpacity
          style={styles.syncButton}
          onPress={triggerSync}
        >
          <Text style={styles.syncButtonText}>🔄 {t('sync_now')}</Text>
        </TouchableOpacity>
      )}
    </ScrollView>
  );
};

// Navegação por abas
const TabNavigator: React.FC = () => (
  <Tabs.Navigator
    screenOptions={{
      tabBarActiveTintColor: '#C9A84C',
      tabBarInactiveTintColor: '#666',
      headerShown: false,
    }}
  >
    <Tabs.Screen
      name="Dashboard"
      component={DashboardScreen}
      options={{
        tabBarLabel: 'Dashboard',
        tabBarIcon: ({ color }) => <Icon name="home" color={color} size={24} />
      }}
    />
    <Tabs.Screen
      name="Plugins"
      component={PluginBrowser}
      options={{
        tabBarLabel: 'Plugins',
        tabBarIcon: ({ color }) => <Icon name="puzzle" color={color} size={24} />
      }}
    />
    <Tabs.Screen
      name="Profile"
      component={ProfileScreen}
      options={{
        tabBarLabel: 'Profile',
        tabBarIcon: ({ color }) => <Icon name="user" color={color} size={24} />
      }}
    />
    <Tabs.Screen
      name="Settings"
      component={SettingsScreen}
      options={{
        tabBarLabel: 'Settings',
        tabBarIcon: ({ color }) => <Icon name="settings" color={color} size={24} />
      }}
    />
  </Tabs.Navigator>
);

// App Principal
export const ArkheMobile: React.FC = () => {
  const [reviewerId, setReviewerId] = useState<string | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const [isOffline, setIsOffline] = useState(false);
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'error'>('idle');

  // Monitorar conectividade
  useEffect(() => {
    const unsubscribe = NetInfo.addEventListener(state => {
      setIsOffline(!state.isConnected);
      if (state.isConnected && authToken) {
        triggerSync();
      }
    });
    return () => unsubscribe();
  }, [authToken]);

  // Sincronização adaptativa
  const triggerSync = useCallback(async () => {
    if (!reviewerId || !authToken) return;

    setSyncStatus('syncing');
    try {
      await OfflineSyncEngine.syncAll(reviewerId, authToken, isOffline);
      setSyncStatus('idle');

      // Notificar conclusão
      if (!isOffline) {
        NotificationService.schedule({
          title: 'Sincronização concluída',
          body: 'Suas revisões foram enviadas para a Catedral',
          delay: 1000,
        });
      }
    } catch (error: any) {
      console.error('Sync failed:', error);
      setSyncStatus('error');
      if (!isOffline) {
        Alert.alert('Erro de sincronização', error.message);
      }
    }
  }, [reviewerId, authToken, isOffline]);

  // Carregar sessão persistente
  useEffect(() => {
    const loadSession = async () => {
      const [token, id] = await Promise.all([
        AsyncStorage.getItem('auth_token'),
        AsyncStorage.getItem('reviewer_id')
      ]);
      if (token && id) {
        setAuthToken(token);
        setReviewerId(id);
      }
    };
    loadSession();
  }, []);

  const handleLogin = (token: string) => {
    setAuthToken(token);
    triggerSync();
  };

  const handleLogout = async () => {
    await AsyncStorage.removeItem("auth_token"); await AsyncStorage.removeItem("reviewer_id"); //(['auth_token', 'reviewer_id']);
    setAuthToken(null);
    setReviewerId(null);
  };

  return (
    <ArkheContext.Provider value={{
      reviewerId,
      authToken,
      isOffline,
      syncStatus,
      setReviewerId,
      setAuthToken,
      triggerSync,
    }}>
      <NavigationContainer>
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          {!authToken ? (
            <Stack.Screen name="Login">
              {() => <LoginScreen onLogin={handleLogin} />}
            </Stack.Screen>
          ) : (
            <>
              <Stack.Screen name="Main" component={TabNavigator} />
              <Stack.Screen name="ReviewDetail" component={ReviewDetailScreen} />
              <Stack.Screen name="PluginDetail" component={PluginDetailScreen} />
            </>
          )}
        </Stack.Navigator>
      </NavigationContainer>
    </ArkheContext.Provider>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#FAF7F0' },
  loginContainer: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#0B1F3A'
  },
  logo: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#C9A84C',
    textAlign: 'center',
    marginBottom: 8
  },
  subtitle: {
    fontSize: 16,
    color: '#fff',
    textAlign: 'center',
    marginBottom: 32,
    opacity: 0.9
  },
  inputContainer: { marginBottom: 24 },
  label: { color: '#fff', marginBottom: 8, fontSize: 14 },
  input: {
    backgroundColor: '#1A3A5C',
    color: '#fff',
    padding: 12,
    borderRadius: 8,
    fontSize: 16
  },
  button: {
    backgroundColor: '#C9A84C',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 16
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#0B1F3A', fontWeight: 'bold', fontSize: 16 },
  header: {
    padding: 16,
    backgroundColor: '#0B1F3A',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  greeting: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  statusBadges: { flexDirection: 'row', gap: 8 },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 6,
    borderRadius: 4,
    gap: 4
  },
  offlineBadge: { backgroundColor: '#C0392B' },
  syncingBadge: { backgroundColor: '#D4AC0D' },
  badgeText: { color: '#fff', fontSize: 12 },
  statsGrid: {
    flexDirection: 'row',
    padding: 16,
    gap: 12
  },
  statCard: {
    flex: 1,
    backgroundColor: '#fff',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2
  },
  statNumber: { fontSize: 24, fontWeight: 'bold', color: '#0B1F3A' },
  statLabel: { fontSize: 12, color: '#666', marginTop: 4 },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0B1F3A',
    padding: 16,
    paddingBottom: 8
  },
  syncButton: {
    margin: 16,
    backgroundColor: '#1A3A5C',
    padding: 14,
    borderRadius: 8,
    alignItems: 'center'
  },
  syncButtonText: { color: '#fff', fontWeight: 'bold' }
});
