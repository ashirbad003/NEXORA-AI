import React, { useState } from 'react';
import { View, ActivityIndicator, StyleSheet } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { LoginScreen } from '../screens/LoginScreen';
import { RegisterScreen } from '../screens/RegisterScreen';
import { BiometricLockScreen } from '../screens/BiometricLockScreen';
import { DashboardScreen } from '../screens/DashboardScreen';
import { DecksScreen } from '../screens/DecksScreen';
import { ReviewSessionScreen } from '../screens/ReviewSessionScreen';
import { MistakeNotebookScreen } from '../screens/MistakeNotebookScreen';
import { HomeScreen } from '../screens/HomeScreen';
import { COLORS } from '../theme/colors';

type AppScreen = 'dashboard' | 'decks' | 'review' | 'mistakes' | 'profile';

export const RootNavigator: React.FC = () => {
  const { isAuthenticated, isLocked, isLoading } = useAuth();
  const [currentAuthView, setCurrentAuthView] = useState<'login' | 'register'>('login');
  const [currentAppScreen, setCurrentAppScreen] = useState<AppScreen>('dashboard');
  const [activeDeckId, setActiveDeckId] = useState<string | undefined>(undefined);

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  // 1. Biometric lock takes highest priority when authenticated
  if (isAuthenticated && isLocked) {
    return <BiometricLockScreen />;
  }

  // 2. Authenticated student workspace
  if (isAuthenticated) {
    switch (currentAppScreen) {
      case 'decks':
        return (
          <DecksScreen
            onSelectDeck={(deckId) => {
              setActiveDeckId(deckId);
              setCurrentAppScreen('review');
            }}
            onBack={() => setCurrentAppScreen('dashboard')}
          />
        );
      case 'review':
        return (
          <ReviewSessionScreen
            deckId={activeDeckId}
            onFinish={() => {
              setActiveDeckId(undefined);
              setCurrentAppScreen('dashboard');
            }}
          />
        );
      case 'mistakes':
        return (
          <MistakeNotebookScreen
            onBack={() => setCurrentAppScreen('dashboard')}
          />
        );
      case 'profile':
        return <HomeScreen />;
      case 'dashboard':
      default:
        return (
          <DashboardScreen
            onNavigateToDecks={() => setCurrentAppScreen('decks')}
            onNavigateToReview={(deckId) => {
              setActiveDeckId(deckId);
              setCurrentAppScreen('review');
            }}
            onNavigateToMistakes={() => setCurrentAppScreen('mistakes')}
          />
        );
    }
  }

  // 3. Unauthenticated flow (Login or Register)
  if (currentAuthView === 'register') {
    return <RegisterScreen onNavigateToLogin={() => setCurrentAuthView('login')} />;
  }

  return <LoginScreen onNavigateToRegister={() => setCurrentAuthView('register')} />;
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
});
