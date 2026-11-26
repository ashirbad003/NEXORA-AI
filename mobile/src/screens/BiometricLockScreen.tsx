import React, { useState } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { COLORS } from '../theme/colors';

export const BiometricLockScreen: React.FC = () => {
  const { unlockWithBiometrics, logout, biometricCapability, user, login } = useAuth();
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isVerifying, setIsVerifying] = useState(false);
  const [showPasswordFallback, setShowPasswordFallback] = useState(false);
  const [fallbackPassword, setFallbackPassword] = useState('');

  const handleUnlock = async () => {
    setErrorMsg(null);
    setIsVerifying(true);
    try {
      const ok = await unlockWithBiometrics();
      if (!ok) {
        setErrorMsg('Biometric verification failed. Please try again or use your password.');
        setShowPasswordFallback(true);
      }
    } finally {
      setIsVerifying(false);
    }
  };

  const handlePasswordUnlock = async () => {
    if (!fallbackPassword) {
      setErrorMsg('Please enter your account password.');
      return;
    }
    setErrorMsg(null);
    setIsVerifying(true);
    try {
      if (!user?.email) {
        await logout();
        return;
      }
      await login({ email: user.email, password: fallbackPassword });
      setFallbackPassword('');
      setShowPasswordFallback(false);
    } catch {
      setErrorMsg('Invalid password. Please re-enter or sign out.');
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <View style={styles.shieldIconContainer}>
          <Text style={styles.shieldIcon}>🔒</Text>
        </View>

        <Text style={styles.title}>NEXORA AI Locked</Text>
        <Text style={styles.subtitle}>
          Welcome back, {user?.full_name || 'Student'}.
        </Text>
        <Text style={styles.instruction}>
          Verify your {biometricCapability?.typeLabel || 'Biometrics'} to continue your session.
        </Text>

        {!!errorMsg && (
          <View style={styles.errorContainer}>
            <Text style={styles.errorText}>{errorMsg}</Text>
          </View>
        )}

        {showPasswordFallback ? (
          <View style={{ width: '100%', marginBottom: 12 }}>
            <Input
              label="Account Password"
              placeholder="••••••••"
              value={fallbackPassword}
              onChangeText={setFallbackPassword}
              secureTextEntry
            />
            <Button
              title="Unlock with Password"
              onPress={handlePasswordUnlock}
              loading={isVerifying}
              style={styles.unlockBtn}
            />
            <Button
              title={`Switch to ${biometricCapability?.typeLabel || 'Biometrics'}`}
              onPress={() => setShowPasswordFallback(false)}
              variant="outline"
              style={{ marginBottom: 8 }}
            />
          </View>
        ) : (
          <>
            <Button
              title={`Unlock with ${biometricCapability?.typeLabel || 'Biometrics'}`}
              onPress={handleUnlock}
              loading={isVerifying}
              style={styles.unlockBtn}
            />
            <Button
              title="Use Password Instead"
              onPress={() => setShowPasswordFallback(true)}
              variant="outline"
              style={{ width: '100%', marginBottom: 8 }}
            />
          </>
        )}

        <Button
          title="Sign Out / Switch Account"
          onPress={logout}
          variant="danger"
          style={styles.logoutBtn}
        />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  content: {
    width: '100%',
    alignItems: 'center',
    backgroundColor: COLORS.backgroundElevated,
    borderRadius: 24,
    padding: 32,
    borderWidth: 1,
    borderColor: COLORS.borderHighlight,
  },
  shieldIconContainer: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: COLORS.primaryGlow,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 20,
    borderWidth: 1,
    borderColor: COLORS.primary,
  },
  shieldIcon: {
    fontSize: 32,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: COLORS.textPrimary,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.primary,
    fontWeight: '600',
    marginBottom: 6,
  },
  instruction: {
    fontSize: 13,
    color: COLORS.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 18,
  },
  errorContainer: {
    backgroundColor: COLORS.dangerGlow,
    borderColor: COLORS.danger,
    borderWidth: 1,
    borderRadius: 8,
    padding: 10,
    marginBottom: 16,
    width: '100%',
  },
  errorText: {
    color: COLORS.danger,
    fontSize: 12,
    textAlign: 'center',
    fontWeight: '500',
  },
  unlockBtn: {
    width: '100%',
    marginBottom: 12,
  },
  logoutBtn: {
    width: '100%',
  },
});
