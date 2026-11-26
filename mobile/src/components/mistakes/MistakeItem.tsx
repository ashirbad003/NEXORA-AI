import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { MistakeEntry } from '../../api/revisionTypes';
import { Card } from '../common/Card';
import { COLORS } from '../../theme/colors';

interface MistakeItemProps {
  mistake: MistakeEntry;
  onResolve: (id: string) => void;
  isResolving?: boolean;
}

export const MistakeItem: React.FC<MistakeItemProps> = ({
  mistake,
  onResolve,
  isResolving = false,
}) => {
  return (
    <Card style={styles.card}>
      <View style={styles.header}>
        <View style={styles.typeBadge}>
          <Text style={styles.typeBadgeText}>
            {mistake.source_type.toUpperCase()}
          </Text>
        </View>
        <Text style={[styles.statusText, mistake.is_resolved ? styles.resolved : styles.unresolved]}>
          {mistake.is_resolved ? 'RESOLVED' : 'UNRESOLVED'}
        </Text>
      </View>

      <Text style={styles.title}>{mistake.title}</Text>

      {!!mistake.question_context && (
        <View style={styles.box}>
          <Text style={styles.boxLabel}>CONTEXT</Text>
          <Text style={styles.boxText}>{mistake.question_context}</Text>
        </View>
      )}

      {!!mistake.error_message && (
        <View style={[styles.box, styles.errorBox]}>
          <Text style={[styles.boxLabel, { color: COLORS.danger }]}>ERROR</Text>
          <Text style={[styles.boxText, { color: COLORS.danger }]}>{mistake.error_message}</Text>
        </View>
      )}

      {!mistake.is_resolved && (
        <TouchableOpacity
          activeOpacity={0.8}
          disabled={isResolving}
          onPress={() => onResolve(mistake.id)}
          style={styles.resolveBtn}
        >
          <Text style={styles.resolveBtnText}>
            {isResolving ? 'Resolving...' : 'Mark as Mastered / Resolved'}
          </Text>
        </TouchableOpacity>
      )}
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    padding: 16,
    marginVertical: 6,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  typeBadge: {
    backgroundColor: COLORS.secondaryGlow,
    borderColor: COLORS.secondary,
    borderWidth: 1,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
  },
  typeBadgeText: {
    fontSize: 9,
    fontWeight: '800',
    color: COLORS.secondary,
  },
  statusText: {
    fontSize: 10,
    fontWeight: '800',
  },
  resolved: {
    color: COLORS.success,
  },
  unresolved: {
    color: COLORS.danger,
  },
  title: {
    fontSize: 15,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  box: {
    backgroundColor: COLORS.backgroundInput,
    borderRadius: 8,
    padding: 10,
    marginVertical: 4,
  },
  errorBox: {
    backgroundColor: COLORS.dangerGlow,
  },
  boxLabel: {
    fontSize: 9,
    fontWeight: '800',
    color: COLORS.textMuted,
    marginBottom: 2,
  },
  boxText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    lineHeight: 16,
  },
  resolveBtn: {
    marginTop: 10,
    height: 36,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: COLORS.primary,
    backgroundColor: COLORS.primaryGlow,
    justifyContent: 'center',
    alignItems: 'center',
  },
  resolveBtnText: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.primary,
  },
});
