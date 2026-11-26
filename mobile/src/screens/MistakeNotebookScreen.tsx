import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { RevisionApi } from '../api/revision';
import { MistakeEntry } from '../api/revisionTypes';
import { MistakeItem } from '../components/mistakes/MistakeItem';
import { COLORS } from '../theme/colors';

interface MistakeNotebookScreenProps {
  onBack: () => void;
}

export const MistakeNotebookScreen: React.FC<MistakeNotebookScreenProps> = ({ onBack }) => {
  const [mistakes, setMistakes] = useState<MistakeEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [filterResolved, setFilterResolved] = useState<boolean | undefined>(false);
  const [resolvingId, setResolvingId] = useState<string | null>(null);

  const loadMistakes = async () => {
    try {
      const data = await RevisionApi.listMistakes(filterResolved);
      setMistakes(data);
    } catch {
      // Offline fallback
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadMistakes();
  }, [filterResolved]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadMistakes();
  };

  const handleResolve = async (id: string) => {
    setResolvingId(id);
    try {
      await RevisionApi.resolveMistake(id);
      await loadMistakes();
    } finally {
      setResolvingId(null);
    }
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onBack} style={styles.backBtn}>
          <Text style={styles.backBtnText}>‹ Back</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Mistake Notebook</Text>
        <View style={{ width: 50 }} />
      </View>

      {/* Filter Tabs */}
      <View style={styles.filterRow}>
        <TouchableOpacity
          onPress={() => setFilterResolved(false)}
          style={[styles.filterTab, filterResolved === false && styles.activeTab]}
        >
          <Text style={[styles.filterText, filterResolved === false && styles.activeFilterText]}>
            Unresolved
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => setFilterResolved(true)}
          style={[styles.filterTab, filterResolved === true && styles.activeTab]}
        >
          <Text style={[styles.filterText, filterResolved === true && styles.activeFilterText]}>
            Resolved
          </Text>
        </TouchableOpacity>

        <TouchableOpacity
          onPress={() => setFilterResolved(undefined)}
          style={[styles.filterTab, filterResolved === undefined && styles.activeTab]}
        >
          <Text style={[styles.filterText, filterResolved === undefined && styles.activeFilterText]}>
            All
          </Text>
        </TouchableOpacity>
      </View>

      {loading ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color={COLORS.primary} />
        </View>
      ) : mistakes.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>✨</Text>
          <Text style={styles.emptyTitle}>Zero Mistakes Here!</Text>
          <Text style={styles.emptySubtext}>
            Mistakes captured during coding arena submissions or assessments will appear here for targeted review.
          </Text>
        </View>
      ) : (
        <FlatList
          data={mistakes}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.listContent}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={handleRefresh} tintColor={COLORS.primary} />}
          renderItem={({ item }) => (
            <MistakeItem
              mistake={item}
              onResolve={handleResolve}
              isResolving={resolvingId === item.id}
            />
          )}
        />
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    paddingTop: 48,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    marginBottom: 12,
  },
  backBtn: {
    paddingVertical: 6,
    paddingHorizontal: 8,
  },
  backBtnText: {
    color: COLORS.primary,
    fontSize: 16,
    fontWeight: '700',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '800',
    color: COLORS.textPrimary,
  },
  filterRow: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    marginBottom: 14,
  },
  filterTab: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: COLORS.backgroundElevated,
    alignItems: 'center',
    marginHorizontal: 3,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  activeTab: {
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primaryGlow,
  },
  filterText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.textSecondary,
  },
  activeFilterText: {
    color: COLORS.primary,
    fontWeight: '800',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  listContent: {
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 6,
  },
  emptySubtext: {
    fontSize: 13,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 18,
  },
});
