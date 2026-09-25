import React from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView, SafeAreaView } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { LanguageProvider, useLanguage } from './src/context/LanguageContext';

function LanguageDemo() {
  const { currentLanguage, changeLanguage, supportedLanguages, t, isLanguageLoading } = useLanguage();

  if (isLanguageLoading) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.loadingText}>Loading language settings...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <Text style={styles.appTitle}>{t('auth:app_name')}</Text>
          <Text style={styles.tagline}>{t('auth:tagline')}</Text>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>{t('common:select_language')}</Text>
          <View style={styles.languageButtonGroup}>
            {supportedLanguages.map((lang) => {
              const isSelected = currentLanguage === lang.code;
              return (
                <TouchableOpacity
                  key={lang.code}
                  style={[styles.languageButton, isSelected && styles.languageButtonActive]}
                  onPress={() => changeLanguage(lang.code)}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.languageButtonText, isSelected && styles.languageButtonTextActive]}>
                    {lang.nativeName} ({lang.label})
                  </Text>
                  {isSelected && <Text style={styles.activeCheck}>✓</Text>}
                </TouchableOpacity>
              );
            })}
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>{t('common:settings')} - Auth Translations</Text>
          <View style={styles.row}>
            <Text style={styles.label}>Login Welcome:</Text>
            <Text style={styles.value}>{t('auth:welcome_title')}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Subtitle:</Text>
            <Text style={styles.value}>{t('auth:welcome_subtitle')}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Phone Field:</Text>
            <Text style={styles.value}>{t('auth:phone_label')}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>OTP Button:</Text>
            <Text style={styles.value}>{t('auth:get_otp')}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Customer Role:</Text>
            <Text style={styles.value}>{t('auth:role_customer_title')}</Text>
          </View>
          <View style={styles.row}>
            <Text style={styles.label}>Worker Role:</Text>
            <Text style={styles.value}>{t('auth:role_worker_title')}</Text>
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.cardTitle}>Common Actions (Buttons)</Text>
          <View style={styles.buttonGrid}>
            <View style={styles.actionBadge}><Text style={styles.actionText}>{t('common:continue')}</Text></View>
            <View style={styles.actionBadge}><Text style={styles.actionText}>{t('common:back')}</Text></View>
            <View style={styles.actionBadge}><Text style={styles.actionText}>{t('common:confirm')}</Text></View>
            <View style={styles.actionBadge}><Text style={styles.actionText}>{t('common:cancel')}</Text></View>
            <View style={styles.actionBadge}><Text style={styles.actionText}>{t('common:retry')}</Text></View>
            <View style={styles.actionBadge}><Text style={styles.actionText}>{t('common:save')}</Text></View>
          </View>
        </View>
      </ScrollView>
      <StatusBar style="auto" />
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <LanguageProvider>
      <LanguageDemo />
    </LanguageProvider>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  centerContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F8FAFC',
  },
  loadingText: {
    fontSize: 16,
    color: '#64748B',
  },
  container: {
    padding: 20,
    paddingTop: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 24,
  },
  appTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 6,
  },
  tagline: {
    fontSize: 14,
    color: '#475569',
    textAlign: 'center',
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 18,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
    borderWidth: 1,
    borderColor: '#E2E8F0',
  },
  cardTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: '#1E293B',
    marginBottom: 14,
  },
  languageButtonGroup: {
    gap: 10,
  },
  languageButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    backgroundColor: '#F8FAFC',
  },
  languageButtonActive: {
    borderColor: '#2563EB',
    backgroundColor: '#EFF6FF',
  },
  languageButtonText: {
    fontSize: 15,
    fontWeight: '500',
    color: '#334155',
  },
  languageButtonTextActive: {
    color: '#1D4ED8',
    fontWeight: '700',
  },
  activeCheck: {
    fontSize: 16,
    color: '#2563EB',
    fontWeight: '700',
  },
  row: {
    marginBottom: 10,
  },
  label: {
    fontSize: 13,
    color: '#64748B',
    fontWeight: '500',
    marginBottom: 2,
  },
  value: {
    fontSize: 15,
    color: '#0F172A',
    fontWeight: '600',
  },
  buttonGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  actionBadge: {
    paddingVertical: 8,
    paddingHorizontal: 14,
    backgroundColor: '#F1F5F9',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  actionText: {
    fontSize: 14,
    color: '#1E293B',
    fontWeight: '500',
  },
});
