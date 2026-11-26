import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  TouchableOpacity,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { COLORS } from '../theme/colors';

interface LoginScreenProps {
  onNavigateToRegister: () => void;
}

export const LoginScreen: React.FC<LoginScreenProps> = ({ onNavigateToRegister }) => {
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleLogin = async () => {
    setErrorMsg(null);
    if (!email.trim() || !password) {
      setErrorMsg('Please enter both email and password.');
      return;
    }

    try {
      await login({ email: email.trim(), password });
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setErrorMsg(detail);
      } else if (Array.isArray(detail) && detail[0]?.msg) {
        setErrorMsg(detail[0].msg);
      } else {
        setErrorMsg('Authentication failed. Please verify credentials.');
      }
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        {/* Brand Header */}
        <View style={styles.header}>
          <Text style={styles.brandTitle}>NEXORA AI</Text>
          <Text style={styles.brandTagline}>Intelligence That Moves You Forward</Text>
        </View>

        {/* Form Container */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Student Login</Text>
          <Text style={styles.cardSubtitle}>Sign in to your learning & placement hub</Text>

          {!!errorMsg && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorBannerText}>{errorMsg}</Text>
            </View>
          )}

          <Input
            label="Email Address"
            placeholder="student@example.com"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
            autoCorrect={false}
          />

          <Input
            label="Password"
            placeholder="••••••••"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          <Button
            title="Authenticate"
            onPress={handleLogin}
            loading={isLoading}
            style={styles.submitBtn}
          />
        </View>

        {/* Footer Navigation */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>New to NEXORA AI? </Text>
          <TouchableOpacity onPress={onNavigateToRegister}>
            <Text style={styles.linkText}>Create Account</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 24,
  },
  header: {
    alignItems: 'center',
    marginBottom: 32,
  },
  brandTitle: {
    fontSize: 32,
    fontWeight: '900',
    color: COLORS.primary,
    letterSpacing: 1.5,
  },
  brandTagline: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 4,
    letterSpacing: 0.5,
  },
  card: {
    backgroundColor: COLORS.backgroundElevated,
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  cardTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  cardSubtitle: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginTop: 4,
    marginBottom: 16,
  },
  errorContainer: {
    backgroundColor: COLORS.dangerGlow,
    borderWidth: 1,
    borderColor: COLORS.danger,
    borderRadius: 8,
    padding: 12,
    marginBottom: 16,
  },
  errorBannerText: {
    color: COLORS.danger,
    fontSize: 13,
    fontWeight: '500',
  },
  submitBtn: {
    marginTop: 12,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 24,
  },
  footerText: {
    color: COLORS.textMuted,
    fontSize: 14,
  },
  linkText: {
    color: COLORS.primary,
    fontWeight: '700',
    fontSize: 14,
  },
});
