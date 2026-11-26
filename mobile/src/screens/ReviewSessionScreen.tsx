import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  TouchableOpacity,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { RevisionApi } from '../api/revision';
import { FlashcardItem } from '../api/revisionTypes';
import { LocalSM2Engine } from '../services/localSm2';
import { generateUUID } from '../services/offlineQueue';
import { FlipCard } from '../components/revision/FlipCard';
import { RatingBar } from '../components/revision/RatingBar';
import { Button } from '../components/common/Button';
import { COLORS } from '../theme/colors';

interface ReviewSessionScreenProps {
  deckId?: string;
  onFinish: () => void;
}

export const ReviewSessionScreen: React.FC<ReviewSessionScreenProps> = ({
  deckId,
  onFinish,
}) => {
  const { user } = useAuth();
  const [cards, setCards] = useState<FlashcardItem[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [reviewedCount, setReviewedCount] = useState(0);
  const [sessionStartTime] = useState(Date.now());
  const [cardStartTime, setCardStartTime] = useState(Date.now());

  useEffect(() => {
    const loadCards = async () => {
      try {
        const due = await RevisionApi.getDueCards(deckId);
        setCards(due);
        setCardStartTime(Date.now());
      } catch {
        // Fallback to empty if error
      } finally {
        setLoading(false);
      }
    };
    loadCards();
  }, [deckId]);

  const currentCard = cards[currentIndex];

  const handleRateCard = async (grade: number) => {
    if (!currentCard || submitting) return;
    setSubmitting(true);

    const timeSpent = Date.now() - cardStartTime;
    // Generate cryptographically strong RFC4122 v4 UUID for server idempotency
    const idempotencyKey = generateUUID();

    // Perform provisional local SM-2 calculation
    LocalSM2Engine.calculate(
      currentCard.repetition || 0,
      currentCard.interval_days || 0,
      currentCard.ease_factor || 2.5,
      currentCard.stability || 1.0,
      grade
    );

    try {
      await RevisionApi.submitReview(
        {
          card_id: currentCard.id,
          grade,
          idempotency_key: idempotencyKey,
          time_spent_ms: timeSpent,
        },
        user?.id || 'current'
      );
    } catch {
      // Handled: enqueued into offline queue by RevisionApi.submitReview
    } finally {
      setReviewedCount((prev) => prev + 1);
      setIsFlipped(false);
      setCurrentIndex((prev) => prev + 1);
      setCardStartTime(Date.now());
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  // Session Completed Screen
  if (!currentCard || currentIndex >= cards.length) {
    const totalMinutes = Math.max(1, Math.round((Date.now() - sessionStartTime) / 60000));
    return (
      <View style={styles.container}>
        <View style={styles.completedContent}>
          <Text style={styles.celebrationIcon}>🎉</Text>
          <Text style={styles.completedTitle}>Revision Complete!</Text>
          <Text style={styles.completedSubtext}>
            You have reviewed all due cards for this session. Excellent memory consolidation!
          </Text>

          <View style={styles.summaryBox}>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryLabel}>CARDS REVIEWED</Text>
              <Text style={styles.summaryValue}>{reviewedCount}</Text>
            </View>
            <View style={styles.summaryItem}>
              <Text style={styles.summaryLabel}>SESSION DURATION</Text>
              <Text style={styles.summaryValue}>{totalMinutes}m</Text>
            </View>
          </View>

          <Button title="Return to Dashboard" onPress={onFinish} style={{ width: '100%', marginTop: 20 }} />
        </View>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {/* Top Header & Progress Indicator */}
      <View style={styles.header}>
        <TouchableOpacity onPress={onFinish} style={styles.closeBtn}>
          <Text style={styles.closeBtnText}>✕ Close</Text>
        </TouchableOpacity>
        <Text style={styles.progressText}>
          Card {currentIndex + 1} of {cards.length}
        </Text>
        <View style={{ width: 50 }} />
      </View>

      {/* Progress Bar */}
      <View style={styles.progressBarTrack}>
        <View
          style={[
            styles.progressBarFill,
            { width: `${((currentIndex + 1) / cards.length) * 100}%` },
          ]}
        />
      </View>

      {/* Flip Card Area */}
      <View style={styles.cardArea}>
        <FlipCard
          prompt={currentCard.prompt}
          answer={currentCard.answer}
          explanation={currentCard.explanation}
          codeSnippet={currentCard.code_snippet}
          isFlipped={isFlipped}
          onFlip={() => setIsFlipped(!isFlipped)}
        />
      </View>

      {/* Bottom Controls */}
      <View style={styles.controlsArea}>
        {isFlipped ? (
          <RatingBar onRate={handleRateCard} disabled={submitting} />
        ) : (
          <Button
            title="Reveal Answer & Rate"
            onPress={() => setIsFlipped(true)}
            style={{ width: '100%' }}
          />
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    paddingTop: 48,
    paddingHorizontal: 20,
    justifyContent: 'space-between',
  },
  center: {
    flex: 1,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  closeBtn: {
    paddingVertical: 6,
    paddingHorizontal: 8,
  },
  closeBtnText: {
    color: COLORS.textMuted,
    fontSize: 14,
    fontWeight: '600',
  },
  progressText: {
    fontSize: 14,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  progressBarTrack: {
    height: 4,
    backgroundColor: COLORS.border,
    borderRadius: 2,
    marginVertical: 12,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: COLORS.primary,
  },
  cardArea: {
    flex: 1,
    justifyContent: 'center',
  },
  controlsArea: {
    paddingBottom: 32,
  },
  completedContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  celebrationIcon: {
    fontSize: 54,
    marginBottom: 16,
  },
  completedTitle: {
    fontSize: 26,
    fontWeight: '900',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  completedSubtext: {
    fontSize: 14,
    color: COLORS.textSecondary,
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 24,
  },
  summaryBox: {
    flexDirection: 'row',
    backgroundColor: COLORS.backgroundElevated,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    padding: 20,
    width: '100%',
    justifyContent: 'space-around',
  },
  summaryItem: {
    alignItems: 'center',
  },
  summaryLabel: {
    fontSize: 10,
    fontWeight: '800',
    color: COLORS.textMuted,
    marginBottom: 4,
  },
  summaryValue: {
    fontSize: 28,
    fontWeight: '900',
    color: COLORS.primary,
  },
});
