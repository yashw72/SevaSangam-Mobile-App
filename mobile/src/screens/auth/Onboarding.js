import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Dimensions,
  FlatList,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import ROUTES from '../../navigation/routes';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

export const OnboardingScreen = ({ navigation }) => {
  const { t } = useTranslation();
  const [currentIndex, setCurrentIndex] = useState(0);
  const flatListRef = useRef(null);

  const slides = [
    {
      id: '1',
      badge: 'Cooperative Verified',
      icon: '🛡️',
      bgColor: '#EFF6FF',
      borderColor: '#DBEAFE',
      iconColor: '#2563EB',
      titleKey: 'auth:slide1_title',
      descKey: 'auth:slide1_desc',
    },
    {
      id: '2',
      badge: 'Fair Share & Welfare',
      icon: '⚖️',
      bgColor: '#ECFDF5',
      borderColor: '#D1FAE5',
      iconColor: '#059669',
      titleKey: 'auth:slide2_title',
      descKey: 'auth:slide2_desc',
    },
    {
      id: '3',
      badge: 'Rapid SOS Dispatch',
      icon: '⚡',
      bgColor: '#FEF3C7',
      borderColor: '#FDE68A',
      iconColor: '#D97706',
      titleKey: 'auth:slide3_title',
      descKey: 'auth:slide3_desc',
    },
  ];

  const handleNext = () => {
    if (currentIndex < slides.length - 1) {
      flatListRef.current?.scrollToIndex({
        index: currentIndex + 1,
        animated: true,
      });
      setCurrentIndex(currentIndex + 1);
    } else {
      handleGetStarted();
    }
  };

  const handleSkip = () => {
    handleGetStarted();
  };

  const handleGetStarted = () => {
    navigation.navigate(ROUTES.AUTH.LOGIN);
  };

  const onMomentumScrollEnd = (event) => {
    const offsetX = event.nativeEvent.contentOffset.x;
    const index = Math.round(offsetX / SCREEN_WIDTH);
    if (index >= 0 && index < slides.length) {
      setCurrentIndex(index);
    }
  };

  const renderSlide = ({ item }) => (
    <View style={styles.slideWrapper}>
      <View style={[styles.illustrationCard, { backgroundColor: item.bgColor, borderColor: item.borderColor }]}>
        <View style={styles.badgeWrapper}>
          <Text style={styles.badgeText}>{item.badge}</Text>
        </View>
        <Text style={styles.slideIcon}>{item.icon}</Text>
      </View>

      <View style={styles.textContainer}>
        <Text style={styles.slideTitle}>{t(item.titleKey)}</Text>
        <Text style={styles.slideDesc}>{t(item.descKey)}</Text>
      </View>
    </View>
  );

  const isLastSlide = currentIndex === slides.length - 1;

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.topBar}>
        <View style={styles.coopBrand}>
          <Text style={styles.brandEmoji}>🤝</Text>
          <Text style={styles.brandTitle}>{t('auth:app_name')}</Text>
        </View>

        {!isLastSlide && (
          <TouchableOpacity onPress={handleSkip} style={styles.skipButton} activeOpacity={0.6}>
            <Text style={styles.skipText}>{t('auth:onboarding_skip')}</Text>
          </TouchableOpacity>
        )}
      </View>

      <FlatList
        ref={flatListRef}
        data={slides}
        renderItem={renderSlide}
        keyExtractor={(item) => item.id}
        horizontal
        pagingEnabled
        showsHorizontalScrollIndicator={false}
        onMomentumScrollEnd={onMomentumScrollEnd}
        style={styles.flatList}
      />

      <View style={styles.footer}>
        {/* Pagination Dots */}
        <View style={styles.dotsContainer}>
          {slides.map((_, index) => (
            <View
              key={index}
              style={[
                styles.dot,
                currentIndex === index ? styles.activeDot : styles.inactiveDot,
              ]}
            />
          ))}
        </View>

        {/* Action Button */}
        <TouchableOpacity
          style={styles.actionButton}
          onPress={handleNext}
          activeOpacity={0.8}
        >
          <Text style={styles.actionButtonText}>
            {isLastSlide ? t('auth:onboarding_get_started') : t('auth:onboarding_next')}
          </Text>
          <Text style={styles.actionArrow}>→</Text>
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
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    paddingTop: 12,
    paddingBottom: 8,
  },
  coopBrand: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  brandEmoji: {
    fontSize: 20,
  },
  brandTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
  },
  skipButton: {
    paddingVertical: 6,
    paddingHorizontal: 12,
  },
  skipText: {
    fontSize: 14,
    color: '#64748B',
    fontWeight: '600',
  },
  flatList: {
    flex: 1,
  },
  slideWrapper: {
    width: SCREEN_WIDTH,
    paddingHorizontal: 24,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 20,
  },
  illustrationCard: {
    width: SCREEN_WIDTH - 64,
    height: 240,
    borderRadius: 24,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 36,
  },
  badgeWrapper: {
    position: 'absolute',
    top: 16,
    backgroundColor: '#FFFFFF',
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#334155',
  },
  slideIcon: {
    fontSize: 80,
  },
  textContainer: {
    alignItems: 'center',
    paddingHorizontal: 12,
  },
  slideTitle: {
    fontSize: 24,
    fontWeight: '800',
    color: '#0F172A',
    textAlign: 'center',
    marginBottom: 12,
    lineHeight: 32,
  },
  slideDesc: {
    fontSize: 15,
    color: '#475569',
    textAlign: 'center',
    lineHeight: 22,
  },
  footer: {
    paddingHorizontal: 24,
    paddingBottom: 28,
    gap: 20,
  },
  dotsContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 8,
  },
  dot: {
    height: 8,
    borderRadius: 4,
  },
  activeDot: {
    width: 24,
    backgroundColor: '#2563EB',
  },
  inactiveDot: {
    width: 8,
    backgroundColor: '#E2E8F0',
  },
  actionButton: {
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
  actionButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  actionArrow: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
});

export default OnboardingScreen;
