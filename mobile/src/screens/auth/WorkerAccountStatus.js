import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';
import ROUTES from '../../navigation/routes';

/**
 * Mock worker data keyed by status — simulates what the backend would return.
 * In production this would come from a hook → service → API call.
 */
const MOCK_WORKER_STATUS_DATA = {
  pending: {
    reason: 'worker:status_reason_pending',
    submittedAt: '2026-09-20',
    certificateCount: 2,
    cooperativeName: 'Mumbai District Labour Cooperative Society',
  },
  rejected: {
    reason: 'worker:status_reason_rejected',
    rejectedAt: '2026-09-22',
    reviewNote: 'worker:status_review_note_rejected',
    certificateCount: 1,
    cooperativeName: 'Pune City Labour Cooperative Society',
  },
  suspended: {
    reason: 'worker:status_reason_suspended',
    suspendedAt: '2026-09-18',
    reviewNote: 'worker:status_review_note_suspended',
    cooperativeName: 'Thane District Labour Cooperative Society',
  },
};

/**
 * Status visual config — icon, colors, i18n label key per status
 */
const STATUS_CONFIG = {
  pending: {
    icon: '⏳',
    badgeBg: '#2563EB',
    badgeBorder: '#1D4ED8',
    iconBg: '#EFF6FF',
    iconBorder: '#DBEAFE',
    labelKey: 'status:pending',
    headingKey: 'worker:account_status_pending_title',
  },
  rejected: {
    icon: '❌',
    badgeBg: '#DC2626',
    badgeBorder: '#B91C1C',
    iconBg: '#FEF2F2',
    iconBorder: '#FECACA',
    labelKey: 'status:rejected',
    headingKey: 'worker:account_status_rejected_title',
  },
  suspended: {
    icon: '⚠️',
    badgeBg: '#D97706',
    badgeBorder: '#B45309',
    iconBg: '#FFFBEB',
    iconBorder: '#FDE68A',
    labelKey: 'status:suspended',
    headingKey: 'worker:account_status_suspended_title',
  },
};

export const WorkerAccountStatusScreen = ({ navigation }) => {
  const { t } = useTranslation();
  const { user, status, logout } = useAuth();

  // Normalise — fallback to pending if status is somehow null
  const currentStatus = ['pending', 'rejected', 'suspended'].includes(status)
    ? status
    : 'pending';

  const config = STATUS_CONFIG[currentStatus];
  const mockData = MOCK_WORKER_STATUS_DATA[currentStatus];

  const canEditProfile = currentStatus === 'pending' || currentStatus === 'rejected';

  const handleEditProfile = () => {
    // Stub navigation — Priti builds the real WorkerProfile screen later
    if (navigation) {
      navigation.navigate(ROUTES.WORKER.PROFILE);
    }
  };

  const handleReuploadCertificates = () => {
    // Stub navigation — Priti builds the real WorkerCertificates screen later
    if (navigation) {
      navigation.navigate(ROUTES.WORKER.CERTIFICATES);
    }
  };

  const handleLogout = async () => {
    await logout();
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Top branding bar */}
        <View style={styles.topBar}>
          <Text style={styles.brandEmoji}>🤝</Text>
          <Text style={styles.brandTitle}>{t('auth:app_name')}</Text>
        </View>

        {/* Status icon */}
        <View style={[styles.iconCircle, { backgroundColor: config.iconBg, borderColor: config.iconBorder }]}>
          <Text style={styles.statusIcon}>{config.icon}</Text>
        </View>

        {/* Status badge */}
        <View style={[styles.statusBadge, { backgroundColor: config.badgeBg }]}>
          <Text style={styles.statusBadgeText}>{t(config.labelKey)}</Text>
        </View>

        {/* Heading */}
        <Text style={styles.heading}>{t(config.headingKey)}</Text>

        {/* Reason from mock data (via i18n) */}
        <Text style={styles.reasonText}>{t(mockData.reason)}</Text>

        {/* Detail info card */}
        <View style={styles.infoCard}>
          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>{t('worker:account_status_label')}</Text>
            <View style={[styles.infoStatusDot, { backgroundColor: config.badgeBg }]} />
            <Text style={[styles.infoValue, { color: config.badgeBg }]}>{t(config.labelKey)}</Text>
          </View>

          {user?.name && (
            <View style={styles.infoRow}>
              <Text style={styles.infoLabel}>{t('worker:name_label')}</Text>
              <Text style={styles.infoValue}>{user.name}</Text>
            </View>
          )}

          <View style={styles.infoRow}>
            <Text style={styles.infoLabel}>{t('worker:cooperative_label')}</Text>
            <Text style={styles.infoValue}>{mockData.cooperativeName}</Text>
          </View>

          {mockData.reviewNote && (
            <View style={styles.reviewNoteBox}>
              <Text style={styles.reviewNoteIcon}>📋</Text>
              <View style={styles.reviewNoteContent}>
                <Text style={styles.reviewNoteLabel}>{t('worker:admin_review_note')}</Text>
                <Text style={styles.reviewNoteText}>{t(mockData.reviewNote)}</Text>
              </View>
            </View>
          )}
        </View>

        {/* Explanation card */}
        <View style={styles.explainCard}>
          <Text style={styles.explainIcon}>💡</Text>
          <Text style={styles.explainText}>{t('worker:account_status_explain')}</Text>
        </View>

        {/* Actions */}
        <View style={styles.actionsContainer}>
          {canEditProfile && (
            <>
              <TouchableOpacity
                style={styles.primaryButton}
                onPress={handleReuploadCertificates}
                activeOpacity={0.8}
              >
                <Text style={styles.primaryButtonIcon}>📄</Text>
                <Text style={styles.primaryButtonText}>{t('worker:reupload_certificates')}</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.secondaryButton}
                onPress={handleEditProfile}
                activeOpacity={0.8}
              >
                <Text style={styles.secondaryButtonIcon}>✏️</Text>
                <Text style={styles.secondaryButtonText}>{t('worker:edit_profile')}</Text>
              </TouchableOpacity>
            </>
          )}

          {currentStatus === 'suspended' && (
            <View style={styles.suspendedNotice}>
              <Text style={styles.suspendedNoticeIcon}>🔒</Text>
              <Text style={styles.suspendedNoticeText}>{t('worker:suspended_contact_notice')}</Text>
            </View>
          )}

          <TouchableOpacity
            style={styles.logoutButton}
            onPress={handleLogout}
            activeOpacity={0.7}
          >
            <Text style={styles.logoutButtonText}>{t('common:logout')}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  scrollContent: {
    padding: 24,
    alignItems: 'center',
    paddingBottom: 48,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 32,
    alignSelf: 'flex-start',
  },
  brandEmoji: {
    fontSize: 22,
  },
  brandTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#0F172A',
  },
  iconCircle: {
    width: 96,
    height: 96,
    borderRadius: 48,
    borderWidth: 2,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 16,
  },
  statusIcon: {
    fontSize: 48,
  },
  statusBadge: {
    paddingVertical: 6,
    paddingHorizontal: 18,
    borderRadius: 20,
    marginBottom: 16,
  },
  statusBadgeText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  heading: {
    fontSize: 22,
    fontWeight: '800',
    color: '#0F172A',
    textAlign: 'center',
    marginBottom: 8,
  },
  reasonText: {
    fontSize: 14,
    color: '#475569',
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: 12,
    marginBottom: 24,
  },
  infoCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 18,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    width: '100%',
    marginBottom: 16,
    gap: 14,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  infoLabel: {
    fontSize: 13,
    color: '#64748B',
    fontWeight: '500',
    flex: 1,
  },
  infoStatusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  infoValue: {
    fontSize: 13,
    color: '#0F172A',
    fontWeight: '600',
    flexShrink: 1,
    textAlign: 'right',
  },
  reviewNoteBox: {
    flexDirection: 'row',
    backgroundColor: '#FEF2F2',
    borderRadius: 12,
    padding: 12,
    gap: 10,
    borderWidth: 1,
    borderColor: '#FECACA',
  },
  reviewNoteIcon: {
    fontSize: 18,
    marginTop: 2,
  },
  reviewNoteContent: {
    flex: 1,
  },
  reviewNoteLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#991B1B',
    marginBottom: 2,
    textTransform: 'uppercase',
    letterSpacing: 0.3,
  },
  reviewNoteText: {
    fontSize: 13,
    color: '#7F1D1D',
    lineHeight: 18,
  },
  explainCard: {
    flexDirection: 'row',
    backgroundColor: '#EFF6FF',
    borderRadius: 12,
    padding: 14,
    gap: 10,
    width: '100%',
    marginBottom: 28,
    borderWidth: 1,
    borderColor: '#DBEAFE',
  },
  explainIcon: {
    fontSize: 18,
  },
  explainText: {
    flex: 1,
    fontSize: 12,
    color: '#1E40AF',
    lineHeight: 18,
  },
  actionsContainer: {
    width: '100%',
    gap: 12,
  },
  primaryButton: {
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
  primaryButtonIcon: {
    fontSize: 18,
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '700',
  },
  secondaryButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
    paddingVertical: 16,
    borderRadius: 14,
    borderWidth: 1.5,
    borderColor: '#CBD5E1',
    gap: 8,
  },
  secondaryButtonIcon: {
    fontSize: 16,
  },
  secondaryButtonText: {
    color: '#334155',
    fontSize: 15,
    fontWeight: '700',
  },
  suspendedNotice: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFBEB',
    borderRadius: 12,
    padding: 14,
    gap: 10,
    borderWidth: 1,
    borderColor: '#FDE68A',
  },
  suspendedNoticeIcon: {
    fontSize: 18,
  },
  suspendedNoticeText: {
    flex: 1,
    fontSize: 13,
    color: '#92400E',
    lineHeight: 18,
  },
  logoutButton: {
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 4,
  },
  logoutButtonText: {
    color: '#EF4444',
    fontSize: 14,
    fontWeight: '600',
  },
});

export default WorkerAccountStatusScreen;
