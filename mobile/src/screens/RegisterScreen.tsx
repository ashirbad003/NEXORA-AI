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

interface RegisterScreenProps {
  onNavigateToLogin: () => void;
}

export const RegisterScreen: React.FC<RegisterScreenProps> = ({ onNavigateToLogin }) => {
  const { register, isLoading } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [institution, setInstitution] = useState('');
  const [department, setDepartment] = useState('');
  const [batchYear, setBatchYear] = useState('');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleRegister = async () => {
    setErrorMsg(null);
    if (!fullName.trim() || !email.trim() || !password) {
      setErrorMsg('Please complete required fields (Name, Email, Password).');
      return;
    }

    if (password.length < 8) {
      setErrorMsg('Password must be at least 8 characters in length.');
      return;
    }

    const parsedBatch = batchYear ? parseInt(batchYear, 10) : undefined;
    if (parsedBatch && (parsedBatch < 2000 || parsedBatch > 2050)) {
      setErrorMsg('Batch year must be between 2000 and 2050.');
      return;
    }

    try {
      await register({
        full_name: fullName.trim(),
        email: email.trim(),
        password,
        institution: institution.trim() || undefined,
        department: department.trim() || undefined,
        batch_year: parsedBatch,
      });
    } catch (err: any) {
      const detail = err.response?.data?.detail;
      if (typeof detail === 'string') {
        setErrorMsg(detail);
      } else if (Array.isArray(detail) && detail[0]?.msg) {
        setErrorMsg(detail[0].msg);
      } else {
        setErrorMsg('Registration failed. Please check inputs.');
      }
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
    >
      <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Text style={styles.brandTitle}>NEXORA AI</Text>
          <Text style={styles.brandTagline}>Student Registration</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Create Student Account</Text>
          <Text style={styles.cardSubtitle}>Access AI-powered career, mock interview & revision tools</Text>

          {!!errorMsg && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorBannerText}>{errorMsg}</Text>
            </View>
          )}

          <Input
            label="Full Name *"
            placeholder="Jane Doe"
            value={fullName}
            onChangeText={setFullName}
          />

          <Input
            label="Email Address *"
            placeholder="jane@university.edu"
            value={email}
            onChangeText={setEmail}
            keyboardType="email-address"
            autoCapitalize="none"
          />

          <Input
            label="Password (min 8 chars) *"
            placeholder="••••••••"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />

          <Input
            label="Institution / University (Optional)"
            placeholder="National Institute of Technology"
            value={institution}
            onChangeText={setInstitution}
          />

          <Input
            label="Department / Major (Optional)"
            placeholder="Computer Science & Engineering"
            value={department}
            onChangeText={setDepartment}
          />

          <Input
            label="Batch Graduation Year (Optional)"
            placeholder="2027"
            value={batchYear}
            onChangeText={setBatchYear}
            keyboardType="numeric"
          />

          <Button
            title="Register & Launch"
            onPress={handleRegister}
            loading={isLoading}
            style={styles.submitBtn}
          />
        </View>

        <View style={styles.footer}>
          <Text style={styles.footerText}>Already have an account? </Text>
          <TouchableOpacity onPress={onNavigateToLogin}>
            <Text style={styles.linkText}>Sign In</Text>
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
    marginBottom: 24,
  },
  brandTitle: {
    fontSize: 28,
    fontWeight: '900',
    color: COLORS.primary,
    letterSpacing: 1.5,
  },
  brandTagline: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 4,
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
    marginBottom: 16,
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
