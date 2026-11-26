import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Switch,
  Alert,
} from 'react-native';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { COLORS } from '../theme/colors';

export const HomeScreen: React.FC = () => {
  const {
    user,
    logout,
    isBiometricEnrolled,
    toggleBiometrics,
    biometricCapability,
    lockSession,
  } = useAuth();

  const [toggling, setToggling] = useState(false);

  const handleToggleBiometrics = async (val: boolean) => {
    setToggling(true);
    const ok = await toggleBiometrics(val);
    setToggling(false);
    if (!ok && val) {
      Alert.alert(
        'Biometrics Unavailable',
        'Could not enable biometrics. Please ensure your device has fingerprint or face recognition configured.'
      );
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.brandTitle}>NEXORA AI</Text>
          <Text style={styles.greeting}>Welcome, {user?.full_name}</Text>
        </View>
        <Button
          title="Lock"
          onPress={lockSession}
          variant="outline"
          style={styles.quickLockBtn}
          textStyle={{ fontSize: 13 }}
        />
      </View>

      {/* Student Readiness Card */}
      <Card style={styles.readinessCard}>
        <Text style={styles.cardHeaderTag}>PHASE 11B ACTIVE SESSION</Text>
        <Text style={styles.readinessTitle}>Student Career Readiness</Text>
        <View style={styles.scoreRow}>
          <Text style={styles.scoreNumber}>
            {user?.student_profile?.readiness_score ?? 0}
          </Text>
          <Text style={styles.scoreTotal}>/ 100</Text>
        </View>
        <Text style={styles.scoreSubtext}>
          Dynamic multi-dimensional index calculated from DSA, system design & mock interviews.
        </Text>
      </Card>

      {/* Profile Details Card */}
      <Card>
        <Text style={styles.sectionTitle}>Account Profile</Text>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Email</Text>
          <Text style={styles.detailValue}>{user?.email}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Role</Text>
          <Text style={styles.detailValue}>{user?.roles?.[0]?.name || 'STUDENT'}</Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Institution</Text>
          <Text style={styles.detailValue}>
            {user?.student_profile?.institution || 'Not set'}
          </Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Department</Text>
          <Text style={styles.detailValue}>
            {user?.student_profile?.department || 'Not set'}
          </Text>
        </View>
        <View style={styles.detailRow}>
          <Text style={styles.detailLabel}>Graduation Batch</Text>
          <Text style={styles.detailValue}>
            {user?.student_profile?.batch_year || 'Not set'}
          </Text>
        </View>
      </Card>

      {/* Security & Biometrics Card */}
      <Card>
        <Text style={styles.sectionTitle}>Hardware Security & Vault</Text>
        <Text style={styles.securitySubtext}>
          Hardware-backed JWT credential storage via Expo SecureStore.
        </Text>

        <View style={styles.biometricRow}>
          <View style={{ flex: 1, paddingRight: 12 }}>
            <Text style={styles.biometricLabel}>
              {biometricCapability?.typeLabel || 'Biometric Authentication'}
            </Text>
            <Text style={styles.biometricDesc}>
              Require biometric verification when resuming NEXORA AI on this device.
            </Text>
          </View>
          <Switch
            value={isBiometricEnrolled}
            onValueChange={handleToggleBiometrics}
            disabled={toggling || !biometricCapability?.hasHardware}
            thumbColor={isBiometricEnrolled ? COLORS.primary : COLORS.textMuted}
            trackColor={{ false: COLORS.border, true: COLORS.primaryGlow }}
          />
        </View>

        {!biometricCapability?.hasHardware && (
          <Text style={styles.warningText}>
            Biometric hardware is not detected on this device. Fallback password security is active.
          </Text>
        )}
      </Card>

      {/* Session Sign Out */}
      <Button
        title="Sign Out"
        onPress={logout}
        variant="danger"
        style={styles.signOutBtn}
      />
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  content: {
    padding: 20,
    paddingTop: 48,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  brandTitle: {
    fontSize: 22,
    fontWeight: '900',
    color: COLORS.primary,
    letterSpacing: 1,
  },
  greeting: {
    fontSize: 16,
    color: COLORS.textPrimary,
    fontWeight: '600',
    marginTop: 2,
  },
  quickLockBtn: {
    height: 36,
    paddingHorizontal: 16,
    marginVertical: 0,
  },
  readinessCard: {
    borderColor: COLORS.borderHighlight,
    backgroundColor: COLORS.backgroundCard,
  },
  cardHeaderTag: {
    fontSize: 11,
    fontWeight: '800',
    color: COLORS.primary,
    letterSpacing: 1,
    marginBottom: 6,
  },
  readinessTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: COLORS.textPrimary,
  },
  scoreRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginVertical: 8,
  },
  scoreNumber: {
    fontSize: 48,
    fontWeight: '900',
    color: COLORS.primary,
  },
  scoreTotal: {
    fontSize: 20,
    fontWeight: '600',
    color: COLORS.textMuted,
    marginLeft: 6,
  },
  scoreSubtext: {
    fontSize: 12,
    color: COLORS.textSecondary,
    lineHeight: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.textPrimary,
    marginBottom: 12,
  },
  detailRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 8,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  detailLabel: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  detailValue: {
    fontSize: 14,
    color: COLORS.textPrimary,
    fontWeight: '600',
  },
  securitySubtext: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginBottom: 16,
  },
  biometricRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  biometricLabel: {
    fontSize: 14,
    color: COLORS.textPrimary,
    fontWeight: '600',
  },
  biometricDesc: {
    fontSize: 12,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  warningText: {
    fontSize: 11,
    color: COLORS.warning,
    marginTop: 8,
  },
  signOutBtn: {
    marginTop: 16,
    marginBottom: 40,
  },
});
