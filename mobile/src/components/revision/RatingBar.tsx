import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { COLORS } from '../../theme/colors';

interface RatingBarProps {
  onRate: (grade: number) => void;
  disabled?: boolean;
}

const RATINGS = [
  { grade: 0, label: 'Blackout', color: '#ef4444', subtitle: '0d' },
  { grade: 1, label: 'Fail', color: '#f97316', subtitle: '0d' },
  { grade: 2, label: 'Hard', color: '#eab308', subtitle: '1d' },
  { grade: 3, label: 'Pass', color: '#84cc16', subtitle: '1d' },
  { grade: 4, label: 'Good', color: COLORS.primary, subtitle: 'Normal' },
  { grade: 5, label: 'Easy', color: '#38bdf8', subtitle: 'Bonus' },
];

export const RatingBar: React.FC<RatingBarProps> = ({ onRate, disabled = false }) => {
  return (
    <View style={styles.container}>
      <Text style={styles.ratingTitle}>Rate Recall Quality (SM-2):</Text>
      <View style={styles.buttonRow}>
        {RATINGS.map((item) => (
          <TouchableOpacity
            key={item.grade}
            activeOpacity={0.7}
            disabled={disabled}
            onPress={() => onRate(item.grade)}
            style={[styles.btn, { borderColor: item.color }]}
          >
            <Text style={[styles.btnGrade, { color: item.color }]}>{item.grade}</Text>
            <Text style={styles.btnLabel}>{item.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 12,
    width: '100%',
  },
  ratingTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: COLORS.textSecondary,
    marginBottom: 8,
    letterSpacing: 0.3,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  btn: {
    flex: 1,
    height: 48,
    marginHorizontal: 3,
    borderRadius: 8,
    backgroundColor: COLORS.backgroundElevated,
    borderWidth: 1.5,
    justifyContent: 'center',
    alignItems: 'center',
  },
  btnGrade: {
    fontSize: 15,
    fontWeight: '800',
  },
  btnLabel: {
    fontSize: 9,
    fontWeight: '600',
    color: COLORS.textMuted,
    marginTop: 1,
  },
});
