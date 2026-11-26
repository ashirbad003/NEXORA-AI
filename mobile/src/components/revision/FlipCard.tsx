import React from 'react';
import {
  TouchableOpacity,
  Text,
  View,
  StyleSheet,
  ScrollView,
} from 'react-native';
import { COLORS } from '../../theme/colors';

interface FlipCardProps {
  prompt: string;
  answer: string;
  explanation?: string | null;
  codeSnippet?: string | null;
  isFlipped: boolean;
  onFlip: () => void;
}

export const FlipCard: React.FC<FlipCardProps> = ({
  prompt,
  answer,
  explanation,
  codeSnippet,
  isFlipped,
  onFlip,
}) => {
  return (
    <TouchableOpacity
      activeOpacity={0.9}
      onPress={onFlip}
      style={[styles.cardContainer, isFlipped && styles.cardFlipped]}
    >
      <View style={styles.cardHeader}>
        <Text style={styles.cardHeaderLabel}>
          {isFlipped ? 'ANSWER & REASONING' : 'QUESTION / PROMPT'}
        </Text>
        <Text style={styles.tapToFlipHint}>
          {isFlipped ? 'Tap to see prompt' : 'Tap to reveal answer'}
        </Text>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        {!isFlipped ? (
          <>
            <Text style={styles.promptText}>{prompt}</Text>
            {!!codeSnippet && (
              <View style={styles.codeContainer}>
                <Text style={styles.codeText}>{codeSnippet}</Text>
              </View>
            )}
          </>
        ) : (
          <>
            <Text style={styles.answerText}>{answer}</Text>
            {!!explanation && (
              <View style={styles.explanationBox}>
                <Text style={styles.explanationHeader}>EXPLANATION</Text>
                <Text style={styles.explanationText}>{explanation}</Text>
              </View>
            )}
          </>
        )}
      </ScrollView>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  cardContainer: {
    backgroundColor: COLORS.backgroundElevated,
    borderRadius: 20,
    borderWidth: 1.5,
    borderColor: COLORS.border,
    padding: 24,
    minHeight: 280,
    maxHeight: 380,
    width: '100%',
    marginVertical: 12,
  },
  cardFlipped: {
    borderColor: COLORS.primary,
    backgroundColor: '#0a1426',
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
    paddingBottom: 8,
  },
  cardHeaderLabel: {
    fontSize: 11,
    fontWeight: '800',
    color: COLORS.primary,
    letterSpacing: 1,
  },
  tapToFlipHint: {
    fontSize: 11,
    color: COLORS.textMuted,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
  },
  promptText: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
    lineHeight: 26,
  },
  answerText: {
    fontSize: 17,
    fontWeight: '600',
    color: COLORS.textPrimary,
    lineHeight: 24,
  },
  codeContainer: {
    backgroundColor: '#03050a',
    borderRadius: 8,
    padding: 12,
    marginTop: 14,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  codeText: {
    fontFamily: 'monospace',
    color: COLORS.primary,
    fontSize: 13,
  },
  explanationBox: {
    backgroundColor: COLORS.backgroundCard,
    borderRadius: 8,
    padding: 12,
    marginTop: 14,
    borderLeftWidth: 3,
    borderLeftColor: COLORS.secondary,
  },
  explanationHeader: {
    fontSize: 10,
    fontWeight: '800',
    color: COLORS.secondary,
    letterSpacing: 0.8,
    marginBottom: 4,
  },
  explanationText: {
    fontSize: 13,
    color: COLORS.textSecondary,
    lineHeight: 18,
  },
});
