import React from 'react';
import { SafeAreaView, StatusBar, StyleSheet } from 'react-native';
import { AuthProvider } from './src/context/AuthContext';
import { RootNavigator } from './src/navigation/RootNavigator';
import { COLORS } from './src/theme/colors';

export default function App() {
  return (
    <AuthProvider>
      <SafeAreaView style={styles.root}>
        <StatusBar barStyle="light-content" backgroundColor={COLORS.background} />
        <RootNavigator />
      </SafeAreaView>
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
});
