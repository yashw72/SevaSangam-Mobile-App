import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useLanguage } from '../../context/LanguageContext';
import ROUTES from '../../navigation/routes';

export const LanguageSelectScreen = ({ navigation }) => {
  const { currentLanguage, changeLanguage, supportedLanguages, t } = useLanguage();

  const handleLanguagePick = (langCode) => {
    changeLanguage(langCode);
  };

  const handleContinue = () => {
    navigation.navigate(ROUTES.AUTH.ONBOARDING);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <View style={styles.globeIconContainer}>
            <Text style={styles.globeIcon}>🌐</Text>
          </View>
          <Text style={styles.title}>{t('common:select_language')}</Text>
          <Text style={styles.subtitle}>
            Choose your preferred language for the SevaSangam experience
          </Text>
        </View>

        <View style={styles.languageList}>
          {supportedLanguages.map((lang) => {
            const isSelected = currentLanguage === lang.code;
            return (
              <TouchableOpacity
                key={lang.code}
                style={[styles.langCard, isSelected && styles.langCardActive]}
                onPress={() => handleLanguagePick(lang.code)}
                activeOpacity={0.7}
              >
                <View style={styles.langInfo}>
                  <Text style={[styles.nativeName, isSelected && styles.nativeNameActive]}>
                    {lang.nativeName}
                  </Text>
                  <Text style={styles.englishLabel}>{lang.label}</Text>
                </View>

                <View style={[styles.radioCircle, isSelected && styles.radioCircleActive]}>
                  {isSelected && <View style={styles.radioDot} />}
                </View>
              </TouchableOpacity>
            );
          })}
        </View>

        <View style={styles.noteBox}>
          <Text style={styles.noteIcon}>💡</Text>
          <Text style={styles.noteText}>
            You can also switch languages anytime from the in-app profile settings.
          </Text>
        </View>
      </ScrollView>

      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={styles.continueButton}
          onPress={handleContinue}
          activeOpacity={0.8}
        >
          <Text style={styles.continueButtonText}>{t('common:continue')}</Text>
          <Text style={styles.arrowIcon}>→</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  container: {
    padding: 24,
    paddingBottom: 100,
  },
  header: {
    alignItems: 'center',
    marginTop: 16,
    marginBottom: 32,
  },
  globeIconContainer: {
    width: 64,
    height: 64,
    borderRadius: 20,
    backgroundColor: '#EFF6FF',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  globeIcon: {
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
    paddingHorizontal: 16,
  },
  languageList: {
    gap: 14,
    marginBottom: 24,
  },
  langCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 18,
    paddingHorizontal: 20,
    borderRadius: 16,
    borderWidth: 1.5,
    borderColor: '#E2E8F0',
    backgroundColor: '#F8FAFC',
  },
  langCardActive: {
    borderColor: '#2563EB',
    backgroundColor: '#EFF6FF',
  },
  langInfo: {
    flex: 1,
  },
  nativeName: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1E293B',
    marginBottom: 2,
  },
  nativeNameActive: {
    color: '#1D4ED8',
  },
  englishLabel: {
    fontSize: 13,
    color: '#64748B',
    fontWeight: '500',
  },
  radioCircle: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: '#CBD5E1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioCircleActive: {
    borderColor: '#2563EB',
  },
  radioDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#2563EB',
  },
  noteBox: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F1F5F9',
    padding: 14,
    borderRadius: 12,
    gap: 10,
  },
  noteIcon: {
    fontSize: 18,
  },
  noteText: {
    flex: 1,
    fontSize: 12,
    color: '#475569',
    lineHeight: 16,
  },
  bottomBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#F1F5F9',
  },
  continueButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2563EB',
    paddingVertical: 16,
    borderRadius: 14,
    gap: 8,
    shadowColor: '#2563EB',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 4,
  },
  continueButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  arrowIcon: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
});

export default LanguageSelectScreen;
