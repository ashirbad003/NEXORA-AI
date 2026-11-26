import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { FlashcardDeck } from '../../api/revisionTypes';
import { Card } from '../common/Card';
import { COLORS } from '../../theme/colors';

interface DeckCardProps {
  deck: FlashcardDeck;
  onPress: () => void;
}

export const DeckCard: React.FC<DeckCardProps> = ({ deck, onPress }) => {
  return (
    <TouchableOpacity activeOpacity={0.8} onPress={onPress}>
      <Card style={styles.container}>
        <View style={styles.headerRow}>
          <Text style={styles.category}>{deck.category.toUpperCase()}</Text>
          {deck.due_card_count > 0 ? (
            <View style={styles.dueBadge}>
              <Text style={styles.dueBadgeText}>{deck.due_card_count} DUE</Text>
            </View>
          ) : (
            <View style={styles.doneBadge}>
              <Text style={styles.doneBadgeText}>UP TO DATE</Text>
            </View>
          )}
        </View>

        <Text style={styles.title}>{deck.title}</Text>
        {!!deck.description && (
          <Text style={styles.description} numberOfLines={2}>
            {deck.description}
          </Text>
        )}

        <View style={styles.footerRow}>
          <Text style={styles.cardCount}>
            {deck.card_count} cards total
          </Text>
          {deck.tags?.length > 0 && (
            <View style={styles.tagsContainer}>
              {deck.tags.slice(0, 2).map((t, i) => (
                <View key={i} style={styles.tag}>
                  <Text style={styles.tagText}>#{t}</Text>
                </View>
              ))}
            </View>
          )}
        </View>
      </Card>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    marginVertical: 6,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  category: {
    fontSize: 10,
    fontWeight: '800',
    color: COLORS.secondary,
    letterSpacing: 0.8,
  },
  dueBadge: {
    backgroundColor: 'rgba(239, 68, 68, 0.2)',
    borderColor: COLORS.danger,
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  dueBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    color: COLORS.danger,
  },
  doneBadge: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderColor: COLORS.success,
    borderWidth: 1,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 2,
  },
  doneBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: COLORS.success,
  },
  title: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 4,
  },
  description: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: 10,
    lineHeight: 18,
  },
  footerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 6,
  },
  cardCount: {
    fontSize: 12,
    color: COLORS.textMuted,
    fontWeight: '500',
  },
  tagsContainer: {
    flexDirection: 'row',
  },
  tag: {
    backgroundColor: COLORS.backgroundInput,
    borderRadius: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginLeft: 4,
  },
  tagText: {
    fontSize: 10,
    color: COLORS.textSecondary,
  },
});
