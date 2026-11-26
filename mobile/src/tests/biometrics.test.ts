import { BiometricService } from '../services/biometrics';
import * as LocalAuthentication from 'expo-local-authentication';

jest.mock('expo-local-authentication', () => ({
  hasHardwareAsync: jest.fn(),
  isEnrolledAsync: jest.fn(),
  supportedAuthenticationTypesAsync: jest.fn(),
  authenticateAsync: jest.fn(),
  AuthenticationType: {
    FINGERPRINT: 1,
    FACIAL_RECOGNITION: 2,
    IRIS: 3,
  },
}));

describe('BiometricService', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('correctly maps hardware and enrollment capabilities for facial recognition', async () => {
    (LocalAuthentication.hasHardwareAsync as jest.Mock).mockResolvedValue(true);
    (LocalAuthentication.isEnrolledAsync as jest.Mock).mockResolvedValue(true);
    (LocalAuthentication.supportedAuthenticationTypesAsync as jest.Mock).mockResolvedValue([
      LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION,
    ]);

    const cap = await BiometricService.checkCapabilities();
    expect(cap.hasHardware).toBe(true);
    expect(cap.isEnrolled).toBe(true);
    expect(cap.typeLabel).toBe('Face ID / Facial Recognition');
  });

  it('returns unavailable when device lacks biometric hardware', async () => {
    (LocalAuthentication.hasHardwareAsync as jest.Mock).mockResolvedValue(false);

    const cap = await BiometricService.checkCapabilities();
    expect(cap.hasHardware).toBe(false);
    expect(cap.isEnrolled).toBe(false);
    expect(cap.typeLabel).toBe('Unavailable');
  });

  it('invokes local authentication with security prompt and returns success', async () => {
    (LocalAuthentication.hasHardwareAsync as jest.Mock).mockResolvedValue(true);
    (LocalAuthentication.isEnrolledAsync as jest.Mock).mockResolvedValue(true);
    (LocalAuthentication.authenticateAsync as jest.Mock).mockResolvedValue({ success: true });

    const ok = await BiometricService.authenticate('Custom unlock prompt');
    expect(ok).toBe(true);
    expect(LocalAuthentication.authenticateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        promptMessage: 'Custom unlock prompt',
        fallbackLabel: 'Use Password',
      })
    );
  });
});
