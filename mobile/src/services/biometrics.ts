import * as LocalAuthentication from 'expo-local-authentication';

export interface BiometricCapability {
  hasHardware: boolean;
  isEnrolled: boolean;
  supportedTypes: LocalAuthentication.AuthenticationType[];
  typeLabel: string;
}

export const BiometricService = {
  /**
   * Evaluates device biometric capability.
   */
  async checkCapabilities(): Promise<BiometricCapability> {
    try {
      const hasHardware = await LocalAuthentication.hasHardwareAsync();
      const isEnrolled = hasHardware ? await LocalAuthentication.isEnrolledAsync() : false;
      const supportedTypes = hasHardware ? await LocalAuthentication.supportedAuthenticationTypesAsync() : [];

      let typeLabel = 'Biometrics';
      if (!hasHardware || !isEnrolled) {
        typeLabel = 'Unavailable';
      } else if (supportedTypes.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) {
        typeLabel = 'Face ID / Facial Recognition';
      } else if (supportedTypes.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) {
        typeLabel = 'Fingerprint / Touch ID';
      } else if (supportedTypes.includes(LocalAuthentication.AuthenticationType.IRIS)) {
        typeLabel = 'Iris Scanner';
      }

      return {
        hasHardware,
        isEnrolled,
        supportedTypes,
        typeLabel,
      };
    } catch {
      return {
        hasHardware: false,
        isEnrolled: false,
        supportedTypes: [],
        typeLabel: 'Unavailable',
      };
    }
  },

  /**
   * Prompts the user for biometric authentication.
   * Biometrics protects local access only and does not bypass server-side token checks.
   */
  async authenticate(promptMessage: string = 'Verify identity to unlock NEXORA AI'): Promise<boolean> {
    try {
      const capability = await this.checkCapabilities();
      if (!capability.hasHardware || !capability.isEnrolled) {
        return false;
      }

      const result = await LocalAuthentication.authenticateAsync({
        promptMessage,
        fallbackLabel: 'Use Password',
        cancelLabel: 'Cancel',
        disableDeviceFallback: false,
      });

      return result.success;
    } catch {
      return false;
    }
  },
};
