import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { RevisionApi } from '../api/revision';
import { RevisionDashboardStats } from '../api/revisionTypes';
import { OfflineQueueService } from '../services/offlineQueue';
import { SyncEngineService, SyncResult } from '../services/syncEngine';
import { PushNotificationService } from '../services/pushNotifications';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { COLORS } from '../theme/colors';

interface DashboardScreenProps {
  onNavigateToDecks: () => void;
  onNavigateToReview: (deckId?: string) => void;
  onNavigateToMistakes: () => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({
  onNavigateToDecks,
  onNavigateToReview,
  onNavigateToMistakes,
}) => {
  const { user, lockSession } = useAuth();
  const [stats, setStats] = useState<RevisionDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [pendingSyncCount, setPendingSyncCount] = useState(0);
  const [isSyncing, setIsSyncing] = useState(false);
  const [lastSyncResult, setLastSyncResult] = useState<SyncResult | null>(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      const data = await RevisionApi.getDashboardStats();
      setStats(data);
      const pending = await OfflineQueueService.getPendingCount(user?.id || 'current');
      setPendingSyncCount(pending);
    } catch {
      // Offline fallback: keep existing data or default zeros
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [user?.id]);

  useEffect(() => {
    fetchDashboardData();
    // Register push notification token on login
    if (user?.id) {
      PushNotificationService.registerForPushNotifications(user.id).catch(() => {});
    }
  }, [fetchDashboardData, user?.id]);

  const handleRefresh = () => {
    setRefreshing(true);
    handleSyncNow();
  };

  const handleSyncNow = async () => {
    setIsSyncing(true);
    try {
      const res = await SyncEngineService.synchronize(user?.id || 'current');
      setLastSyncResult(res);
      await fetchDashboardData();
    } catch {
      // Re-fetch pending count even on partial failure
      const pending = await OfflineQueueService.getPendingCount(user?.id || 'current');
      setPendingSyncCount(pending);
    } finally {
      setIsSyncing(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor={COLORS.primary} />}
    >
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.brandTitle}>NEXORA AI</Text>
          <Text style={styles.greeting}>{user?.full_name}</Text>
        </View>
        <TouchableOpacity onPress={lockSession} style={styles.lockBtn}>
          <Text style={styles.lockIcon}>🔒</Text>
        </TouchableOpacity>
      </View>

      {/* Offline Sync Banner if pending operations exist */}
      {pendingSyncCount > 0 && (
        <Card style={styles.syncCard}>
          <View style={styles.syncRow}>
            <View style={{ flex: 1 }}>
              <Text style={styles.syncTitle}>⚡ {pendingSyncCount} Offline Reviews Pending</Text>
              <Text style={styles.syncSubtext}>Saved in local vault. Ready to reconcile with server.</Text>
            </View>
            <Button
              title={isSyncing ? 'Syncing...' : 'Sync Now'}
              onPress={handleSyncNow}
              loading={isSyncing}
              style={styles.syncBtn}
              textStyle={{ fontSize: 12 }}
            />
          </View>
        </Card>
      )}

      {/* Main Readiness Score Card */}
      <Card style={styles.readinessCard}>
        <Text style={styles.cardHeaderTag}>CAREER READINESS INDEX</Text>
        <View style={styles.scoreRow}>
          <Text style={styles.scoreNumber}>{user?.student_profile?.readiness_score ?? 0}</Text>
          <Text style={styles.scoreTotal}>/ 100</Text>
        </View>
        <Text style={styles.scoreSubtext}>
          Dynamic multi-dimensional index calculated from DSA, system design & mock interviews.
        </Text>
      </Card>

      {/* Revision Stats Metrics Grid */}
      <View style={styles.statsGrid}>
        <Card style={styles.statBox}>
          <Text style={styles.statLabel}>CARDS DUE</Text>
          <Text style={[styles.statValue, { color: (stats?.due_cards_count ?? 0) > 0 ? COLORS.danger : COLORS.success }]}>
            {stats?.due_cards_count ?? 0}
          </Text>
          <Text style={styles.statDesc}>Requires review</Text>
        </Card>

        <Card style={styles.statBox}>
          <Text style={styles.statLabel}>STREAK</Text>
          <Text style={[styles.statValue, { color: COLORS.primary }]}>
            {stats?.current_streak_days ?? 0}d
          </Text>
          <Text style={styles.statDesc}>Active study days</Text>
        </Card>
      </View>

      <View style={styles.statsGrid}>
        <Card style={styles.statBox}>
          <Text style={styles.statLabel}>REVIEWED TODAY</Text>
          <Text style={styles.statValue}>{stats?.cards_reviewed_today ?? 0}</Text>
          <Text style={styles.statDesc}>Flashcards</Text>
        </Card>

        <Card style={styles.statBox}>
          <Text style={styles.statLabel}>RETENTION</Text>
          <Text style={styles.statValue}>{stats?.retention_rate_pct ?? 0}%</Text>
          <Text style={styles.statDesc}>SM-2 recall rate</Text>
        </Card>
      </View>

      {/* Primary Action Button */}
      {(stats?.due_cards_count ?? 0) > 0 ? (
        <Button
          title={`Start Daily Revision (${stats?.due_cards_count} Due)`}
          onPress={() => onNavigateToReview()}
          style={styles.actionBtn}
        />
      ) : (
        <Button
          title="Browse Flashcard Decks"
          onPress={onNavigateToDecks}
          variant="outline"
          style={styles.actionBtn}
        />
      )}

      {/* Module Navigation Shortcuts */}
      <Text style={styles.sectionHeader}>Revision Modules</Text>

      <TouchableOpacity activeOpacity={0.8} onPress={onNavigateToDecks}>
        <Card style={styles.menuCard}>
          <View>
            <Text style={styles.menuTitle}>📚 Flashcard Decks Catalog</Text>
            <Text style={styles.menuDesc}>Curated DSA, system architecture & core engineering decks</Text>
          </View>
          <Text style={styles.menuArrow}>›</Text>
        </Card>
      </TouchableOpacity>

      <TouchableOpacity activeOpacity={0.8} onPress={onNavigateToMistakes}>
        <Card style={styles.menuCard}>
          <View>
            <Text style={styles.menuTitle}>📓 Mistake Notebook</Text>
            <Text style={styles.menuDesc}>Coding bugs & assessment weak spots earmarked for mastery</Text>
          </View>
          <Text style={styles.menuArrow}>›</Text>
        </Card>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  centerContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    padding: 20,
    paddingTop: 48,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  brandTitle: {
    fontSize: 22,
    fontWeight: '900',
    color: COLORS.primary,
    letterSpacing: 1,
  },
  greeting: {
    fontSize: 16,
    color: COLORS.textPrimary,
    fontWeight: '600',
    marginTop: 2,
  },
  lockBtn: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: COLORS.backgroundElevated,
    borderWidth: 1,
    borderColor: COLORS.border,
    justifyContent: 'center',
    alignItems: 'center',
  },
  lockIcon: {
    fontSize: 18,
  },
  syncCard: {
    backgroundColor: 'rgba(234, 179, 8, 0.1)',
    borderColor: '#eab308',
    padding: 12,
    marginBottom: 8,
  },
  syncRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  syncTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#eab308',
  },
  syncSubtext: {
    fontSize: 11,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  syncBtn: {
    height: 34,
    paddingHorizontal: 12,
    marginVertical: 0,
    backgroundColor: '#eab308',
  },
  readinessCard: {
    backgroundColor: COLORS.backgroundCard,
    borderColor: COLORS.borderHighlight,
    marginBottom: 8,
  },
  cardHeaderTag: {
    fontSize: 10,
    fontWeight: '800',
    color: COLORS.primary,
    letterSpacing: 1,
    marginBottom: 4,
  },
  scoreRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginVertical: 4,
  },
  scoreNumber: {
    fontSize: 44,
    fontWeight: '900',
    color: COLORS.primary,
  },
  scoreTotal: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.textMuted,
    marginLeft: 6,
  },
  scoreSubtext: {
    fontSize: 12,
    color: COLORS.textSecondary,
    lineHeight: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statBox: {
    flex: 1,
    marginHorizontal: 4,
    padding: 14,
  },
  statLabel: {
    fontSize: 10,
    fontWeight: '800',
    color: COLORS.textMuted,
    letterSpacing: 0.5,
  },
  statValue: {
    fontSize: 26,
    fontWeight: '900',
    color: COLORS.textPrimary,
    marginVertical: 4,
  },
  statDesc: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  actionBtn: {
    marginVertical: 12,
  },
  sectionHeader: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginTop: 14,
    marginBottom: 6,
  },
  menuCard: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    marginVertical: 6,
  },
  menuTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  menuDesc: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginTop: 2,
    maxWidth: 260,
  },
  menuArrow: {
    fontSize: 24,
    color: COLORS.textMuted,
    fontWeight: '300',
  },
});
