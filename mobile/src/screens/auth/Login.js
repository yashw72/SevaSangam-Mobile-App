import React, { useState } from 'react';
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
import ROUTES from '../../navigation/routes';

export const LoginScreen = ({ navigation }) => {
  const { t } = useTranslation();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [errorText, setErrorText] = useState('');

  const handlePhoneChange = (text) => {
    // Only allow numbers and limit to 10 digits
    const cleaned = text.replace(/[^0-9]/g, '').slice(0, 10);
    setPhoneNumber(cleaned);
    if (errorText) setErrorText('');
  };

  const handleGetOtp = () => {
    if (phoneNumber.length !== 10) {
      setErrorText(t('errors:invalid_phone'));
      return;
    }
    setErrorText('');
    navigation.navigate(ROUTES.AUTH.VERIFY_OTP, {
      phone: `+91 ${phoneNumber}`,
      rawPhone: phoneNumber,
    });
  };

  // Demo shortcut helper for testing
  const handleQuickFill = (num) => {
    setPhoneNumber(num);
    setErrorText('');
  };

  const isValid = phoneNumber.length === 10;

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.flex}
      >
        <ScrollView contentContainerStyle={styles.container} keyboardShouldPersistTaps="handled">
          <View style={styles.header}>
            <View style={styles.iconContainer}>
              <Text style={styles.appIcon}>📱</Text>
            </View>
            <Text style={styles.title}>{t('auth:welcome_title')}</Text>
            <Text style={styles.subtitle}>{t('auth:welcome_subtitle')}</Text>
          </View>

          <View style={styles.formCard}>
            <Text style={styles.inputLabel}>{t('auth:phone_label')}</Text>

            <View style={[styles.inputRow, errorText ? styles.inputRowError : null]}>
              <View style={styles.countryCodeBadge}>
                <Text style={styles.flagIcon}>🇮🇳</Text>
                <Text style={styles.countryCodeText}>+91</Text>
              </View>

              <TextInput
                style={styles.textInput}
                placeholder={t('auth:phone_placeholder')}
                placeholderTextColor="#94A3B8"
                keyboardType="phone-pad"
                value={phoneNumber}
                onChangeText={handlePhoneChange}
                maxLength={10}
                autoFocus
              />
            </View>

            {errorText ? <Text style={styles.errorText}>{errorText}</Text> : null}

            <TouchableOpacity
              style={[styles.submitButton, !isValid && styles.submitButtonDisabled]}
              onPress={handleGetOtp}
              disabled={!isValid}
              activeOpacity={0.8}
            >
              <Text style={styles.submitButtonText}>{t('auth:get_otp')}</Text>
              <Text style={styles.submitArrow}>→</Text>
            </TouchableOpacity>
          </View>

          {/* Demo Logins Section */}
          <View style={styles.demoSection}>
            <Text style={styles.demoSectionTitle}>⚡ Quick Demo Fill</Text>
            <View style={styles.demoGrid}>
              <TouchableOpacity
                style={styles.demoChip}
                onPress={() => handleQuickFill('9876543210')}
              >
                <Text style={styles.demoChipText}>👤 Customer (..3210)</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.demoChip}
                onPress={() => handleQuickFill('9876543211')}
              >
                <Text style={styles.demoChipText}>🛠️ Worker (..3211)</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.demoChip}
                onPress={() => handleQuickFill('9876543212')}
              >
                <Text style={styles.demoChipText}>⏳ Pending (..3212)</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={styles.demoChip}
                onPress={() => handleQuickFill('9876543213')}
              >
                <Text style={styles.demoChipText}>📊 Admin (..3213)</Text>
              </TouchableOpacity>
            </View>
          </View>

          <View style={styles.footer}>
            <Text style={styles.termsText}>{t('auth:terms_notice')}</Text>
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
    justifyContent: 'space-between',
  },
  header: {
    alignItems: 'center',
    marginTop: 12,
    marginBottom: 28,
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
    marginBottom: 6,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
    textAlign: 'center',
  },
  formCard: {
    marginBottom: 24,
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 8,
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#CBD5E1',
    borderRadius: 14,
    backgroundColor: '#F8FAFC',
    overflow: 'hidden',
    marginBottom: 8,
  },
  inputRowError: {
    borderColor: '#EF4444',
  },
  countryCodeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#E2E8F0',
    paddingVertical: 14,
    paddingHorizontal: 14,
    borderRightWidth: 1,
    borderRightColor: '#CBD5E1',
    gap: 6,
  },
  flagIcon: {
    fontSize: 18,
  },
  countryCodeText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#1E293B',
  },
  textInput: {
    flex: 1,
    paddingVertical: 14,
    paddingHorizontal: 16,
    fontSize: 16,
    fontWeight: '600',
    color: '#0F172A',
    letterSpacing: 1,
  },
  errorText: {
    color: '#EF4444',
    fontSize: 12,
    marginBottom: 12,
    fontWeight: '500',
  },
  submitButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2563EB',
    paddingVertical: 16,
    borderRadius: 14,
    gap: 8,
    marginTop: 12,
    shadowColor: '#2563EB',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
  },
  submitButtonDisabled: {
    backgroundColor: '#94A3B8',
    shadowOpacity: 0,
    elevation: 0,
  },
  submitButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  submitArrow: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
  demoSection: {
    backgroundColor: '#F1F5F9',
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 24,
  },
  demoSectionTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#475569',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    marginBottom: 10,
  },
  demoGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  demoChip: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  demoChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#334155',
  },
  footer: {
    alignItems: 'center',
    marginTop: 'auto',
    paddingTop: 16,
  },
  termsText: {
    fontSize: 12,
    color: '#94A3B8',
    textAlign: 'center',
    lineHeight: 18,
    paddingHorizontal: 16,
  },
});

export default LoginScreen;
