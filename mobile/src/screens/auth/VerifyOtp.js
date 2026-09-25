import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import ROUTES from '../../navigation/routes';

export const VerifyOtpScreen = ({ route, navigation }) => {
  const { t } = useTranslation();
  const { login } = useAuth();
  const phone = route.params?.phone || '+91 9876543210';
  const rawPhone = route.params?.rawPhone || '9876543210';

  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [errorText, setErrorText] = useState('');
  const [resendTimer, setResendTimer] = useState(30);
  const inputRefs = useRef([]);

  // Countdown timer for Resend OTP
  useEffect(() => {
    let interval = null;
    if (resendTimer > 0) {
      interval = setInterval(() => {
        setResendTimer((prev) => prev - 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [resendTimer]);

  const handleOtpChange = (value, index) => {
    const cleaned = value.replace(/[^0-9]/g, '');
    
    // Handle paste of full 6-digit code
    if (cleaned.length > 1) {
      const codeDigits = cleaned.slice(0, 6).split('');
      const newOtp = [...otp];
      codeDigits.forEach((digit, i) => {
        newOtp[i] = digit;
      });
      setOtp(newOtp);
      setErrorText('');
      if (inputRefs.current[5]) {
        inputRefs.current[5].focus();
      }
      return;
    }

    const newOtp = [...otp];
    newOtp[index] = cleaned;
    setOtp(newOtp);
    setErrorText('');

    // Auto advance to next input
    if (cleaned && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handleKeyPress = (e, index) => {
    if (e.nativeEvent.key === 'Backspace' && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerify = async () => {
    const enteredCode = otp.join('');
    if (enteredCode.length < 6) {
      setErrorText('Please enter all 6 digits of the OTP.');
      return;
    }

    // Mock verification: accept "123456"
    if (enteredCode !== '123456') {
      setErrorText(t('auth:invalid_otp_error'));
      return;
    }

    setErrorText('');

    // Detect if this is a recognized demo phone number
    if (rawPhone.endsWith('3210')) {
      await login({ role: 'customer', name: 'Pooja Sharma (Customer)', phone });
    } else if (rawPhone.endsWith('3211')) {
      await login({ role: 'worker', status: 'verified', name: 'Ramesh Kumar (Worker)', phone });
    } else if (rawPhone.endsWith('3212')) {
      await login({ role: 'worker', status: 'pending', name: 'Suresh Patil (Pending)', phone });
    } else if (rawPhone.endsWith('3213')) {
      await login({ role: 'admin', status: 'verified', name: 'Cooperative Admin', phone });
    } else {
      // New / Unknown user -> Choose Profile (Customer / Worker)
      navigation.navigate(ROUTES.AUTH.ROLE_SELECT, { phone });
    }
  };

  const handleResend = () => {
    if (resendTimer === 0) {
      setResendTimer(30);
      setOtp(['', '', '', '', '', '']);
      setErrorText('');
      inputRefs.current[0]?.focus();
    }
  };

  const handleAutoFillMockCode = () => {
    setOtp(['1', '2', '3', '4', '5', '6']);
    setErrorText('');
  };

  const isComplete = otp.every((digit) => digit !== '');

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <View style={styles.iconContainer}>
              <Text style={styles.appIcon}>🔐</Text>
            </View>
            <Text style={styles.title}>{t('auth:verify_title')}</Text>
            <Text style={styles.subtitle}>
              {t('auth:verify_subtitle')} <Text style={styles.phoneBold}>{phone}</Text>
            </Text>

            <TouchableOpacity
              onPress={() => navigation.navigate(ROUTES.AUTH.LOGIN)}
              style={styles.changePhoneButton}
            >
              <Text style={styles.changePhoneText}>{t('auth:change_number')}</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.otpCard}>
            <Text style={styles.otpLabel}>{t('auth:otp_label')}</Text>

            {/* 6 OTP digit boxes */}
            <View style={styles.otpRow}>
              {otp.map((digit, index) => (
                <TextInput
                  key={index}
                  ref={(ref) => (inputRefs.current[index] = ref)}
                  style={[
                    styles.otpBox,
                    digit ? styles.otpBoxFilled : null,
                    errorText ? styles.otpBoxError : null,
                  ]}
                  keyboardType="number-pad"
                  maxLength={index === 0 ? 6 : 1}
                  value={digit}
                  onChangeText={(val) => handleOtpChange(val, index)}
                  onKeyPress={(e) => handleKeyPress(e, index)}
                  selectTextOnFocus
                  autoFocus={index === 0}
                />
              ))}
            </View>

            {errorText ? <Text style={styles.errorText}>{errorText}</Text> : null}

            {/* Mock Code Shortcut */}
            <TouchableOpacity
              style={styles.mockFillButton}
              onPress={handleAutoFillMockCode}
              activeOpacity={0.7}
            >
              <Text style={styles.mockFillText}>⚡ Tap to auto-fill mock code (123456)</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.verifyButton, !isComplete && styles.verifyButtonDisabled]}
              onPress={handleVerify}
              disabled={!isComplete}
              activeOpacity={0.8}
            >
              <Text style={styles.verifyButtonText}>{t('auth:verify_btn')}</Text>
            </TouchableOpacity>

            {/* Resend Countdown / Button */}
            <View style={styles.resendContainer}>
              <Text style={styles.resendPrompt}>{t('auth:resend_prompt')}</Text>
              {resendTimer > 0 ? (
                <Text style={styles.timerText}>
                  {t('auth:resend_timer', { seconds: resendTimer })}
                </Text>
              ) : (
                <TouchableOpacity onPress={handleResend} activeOpacity={0.7}>
                  <Text style={styles.resendLink}>{t('auth:resend_btn')}</Text>
                </TouchableOpacity>
              )}
            </View>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  flex: {
    flex: 1,
  },
  container: {
    padding: 24,
    flexGrow: 1,
  },
  header: {
    alignItems: 'center',
    marginTop: 12,
    marginBottom: 32,
  },
  iconContainer: {
    width: 64,
    height: 64,
    borderRadius: 20,
    backgroundColor: '#EFF6FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  appIcon: {
    fontSize: 32,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
    textAlign: 'center',
    lineHeight: 20,
  },
  phoneBold: {
    fontWeight: '700',
    color: '#0F172A',
  },
  changePhoneButton: {
    marginTop: 8,
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  changePhoneText: {
    color: '#2563EB',
    fontSize: 13,
    fontWeight: '600',
  },
  otpCard: {
    alignItems: 'center',
  },
  otpLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 16,
  },
  otpRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    width: '100%',
    marginBottom: 16,
    gap: 8,
  },
  otpBox: {
    flex: 1,
    height: 56,
    borderWidth: 1.5,
    borderColor: '#CBD5E1',
    borderRadius: 12,
    backgroundColor: '#F8FAFC',
    textAlign: 'center',
    fontSize: 22,
    fontWeight: '700',
    color: '#0F172A',
  },
  otpBoxFilled: {
    borderColor: '#2563EB',
    backgroundColor: '#EFF6FF',
  },
  otpBoxError: {
    borderColor: '#EF4444',
  },
  errorText: {
    color: '#EF4444',
    fontSize: 13,
    fontWeight: '500',
    marginBottom: 16,
    textAlign: 'center',
  },
  mockFillButton: {
    backgroundColor: '#F1F5F9',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 24,
  },
  mockFillText: {
    fontSize: 12,
    color: '#475569',
    fontWeight: '600',
  },
  verifyButton: {
    width: '100%',
    backgroundColor: '#2563EB',
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#2563EB',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
    marginBottom: 24,
  },
  verifyButtonDisabled: {
    backgroundColor: '#94A3B8',
    shadowOpacity: 0,
    elevation: 0,
  },
  verifyButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  resendContainer: {
    alignItems: 'center',
    gap: 6,
  },
  resendPrompt: {
    fontSize: 13,
    color: '#64748B',
  },
  timerText: {
    fontSize: 13,
    color: '#94A3B8',
    fontWeight: '600',
  },
  resendLink: {
    fontSize: 14,
    color: '#2563EB',
    fontWeight: '700',
  },
});

export default VerifyOtpScreen;
