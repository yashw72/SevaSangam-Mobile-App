import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Easing } from 'react-native';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import ROUTES from '../../navigation/routes';

export const SplashScreen = ({ navigation }) => {
  const { t } = useTranslation();
  const { token, isLoading } = useAuth();

  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.85)).current;
  const slideAnim = useRef(new Animated.Value(20)).current;

  useEffect(() => {
    // Start entrance animation
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 900,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
      Animated.timing(scaleAnim, {
        toValue: 1,
        duration: 900,
        easing: Easing.out(Easing.back(1.5)),
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 900,
        easing: Easing.out(Easing.cubic),
        useNativeDriver: true,
      }),
    ]).start();

    // After animation and session restore, transition if still on splash
    const timer = setTimeout(() => {
      if (!isLoading && !token) {
        navigation.replace(ROUTES.AUTH.LANGUAGE_SELECT);
      }
    }, 2000);

    return () => clearTimeout(timer);
  }, [fadeAnim, scaleAnim, slideAnim, isLoading, token, navigation]);

  return (
    <View style={styles.container}>
      <Animated.View
        style={[
          styles.content,
          {
            opacity: fadeAnim,
            transform: [{ scale: scaleAnim }, { translateY: slideAnim }],
          },
        ]}
      >
        <View style={styles.logoBadge}>
          <Text style={styles.logoIcon}>🤝</Text>
        </View>

        <Text style={styles.appName}>{t('auth:app_name')}</Text>
        
        <View style={styles.taglineWrapper}>
          <Text style={styles.tagline}>{t('auth:tagline')}</Text>
        </View>
      </Animated.View>

      <Animated.View style={[styles.footer, { opacity: fadeAnim }]}>
        <View style={styles.trustBadge}>
          <Text style={styles.trustBadgeDot}>•</Text>
          <Text style={styles.trustBadgeText}>Labour Cooperative Societies Platform</Text>
          <Text style={styles.trustBadgeDot}>•</Text>
        </View>
        <Text style={styles.subFooterText}>Ministry of Cooperation • SIH 26089</Text>
      </Animated.View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0F172A', // Sleek dark slate
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  content: {
    alignItems: 'center',
  },
  logoBadge: {
    width: 96,
    height: 96,
    borderRadius: 28,
    backgroundColor: 'rgba(37, 99, 235, 0.18)',
    borderWidth: 1.5,
    borderColor: 'rgba(59, 130, 246, 0.45)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    shadowColor: '#3B82F6',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.35,
    shadowRadius: 16,
    elevation: 8,
  },
  logoIcon: {
    fontSize: 48,
  },
  appName: {
    fontSize: 34,
    fontWeight: '800',
    color: '#FFFFFF',
    letterSpacing: 0.5,
    marginBottom: 8,
  },
  taglineWrapper: {
    paddingHorizontal: 20,
  },
  tagline: {
    fontSize: 14,
    color: '#94A3B8',
    textAlign: 'center',
    lineHeight: 22,
    fontWeight: '400',
  },
  footer: {
    position: 'absolute',
    bottom: 36,
    alignItems: 'center',
  },
  trustBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(30, 41, 59, 0.8)',
    paddingVertical: 6,
    paddingHorizontal: 14,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(51, 65, 85, 0.6)',
    marginBottom: 6,
  },
  trustBadgeDot: {
    color: '#38BDF8',
    fontSize: 12,
    marginHorizontal: 4,
  },
  trustBadgeText: {
    color: '#CBD5E1',
    fontSize: 12,
    fontWeight: '500',
    letterSpacing: 0.3,
  },
  subFooterText: {
    fontSize: 11,
    color: '#64748B',
    fontWeight: '400',
  },
});

export default SplashScreen;
