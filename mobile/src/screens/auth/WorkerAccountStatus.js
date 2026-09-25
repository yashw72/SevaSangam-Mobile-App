import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export const WorkerAccountStatusScreen = ({
  status = 'pending', // 'pending' | 'rejected' | 'suspended'
  reason = 'Your trade certificate is currently under review by the Cooperative Administrator.',
  onEditProfile,
  onReuploadCertificates,
  onLogout,
}) => {
  const getStatusBadge = () => {
    switch (status) {
      case 'rejected':
        return { color: '#EF4444', label: 'Application Rejected', icon: '❌' };
      case 'suspended':
        return { color: '#F59E0B', label: 'Account Suspended', icon: '⚠️' };
      case 'pending':
      default:
        return { color: '#3B82F6', label: 'Verification Pending', icon: '⏳' };
    }
  };

  const badge = getStatusBadge();

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.container}>
        <View style={styles.iconContainer}>
          <Text style={styles.largeIcon}>{badge.icon}</Text>
        </View>

        <View style={[styles.badge, { backgroundColor: badge.color }]}>
          <Text style={styles.badgeText}>{badge.label}</Text>
        </View>

        <Text style={styles.title}>Account Status</Text>
        <Text style={styles.reason}>{reason}</Text>

        <View style={styles.infoCard}>
          <Text style={styles.infoTitle}>Why is my account in this state?</Text>
          <Text style={styles.infoText}>
            Labour Cooperative Societies verify every worker's credentials and trade certificates
            to ensure fair job distribution and high trust.
          </Text>
        </View>

        <View style={styles.actions}>
          {status !== 'suspended' && (
            <>
              <TouchableOpacity
                style={styles.primaryButton}
                onPress={onReuploadCertificates || (() => alert('Re-upload certificates action'))}
                activeOpacity={0.7}
              >
                <Text style={styles.primaryButtonText}>Re-upload Certificates</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.secondaryButton}
                onPress={onEditProfile || (() => alert('Edit profile action'))}
                activeOpacity={0.7}
              >
                <Text style={styles.secondaryButtonText}>Edit Profile</Text>
              </TouchableOpacity>
            </>
          )}

          <TouchableOpacity
            style={styles.logoutButton}
            onPress={onLogout || (() => alert('Logout clicked'))}
            activeOpacity={0.7}
          >
            <Text style={styles.logoutButtonText}>Log Out</Text>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  container: {
    flex: 1,
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconContainer: {
    marginBottom: 16,
  },
  largeIcon: {
    fontSize: 54,
  },
  badge: {
    paddingVertical: 6,
    paddingHorizontal: 16,
    borderRadius: 20,
    marginBottom: 16,
  },
  badgeText: {
    color: '#FFFFFF',
    fontWeight: '700',
    fontSize: 13,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
  },
  reason: {
    fontSize: 14,
    color: '#475569',
    textAlign: 'center',
    marginBottom: 24,
    lineHeight: 20,
    paddingHorizontal: 12,
  },
  infoCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 32,
    width: '100%',
  },
  infoTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1E293B',
    marginBottom: 6,
  },
  infoText: {
    fontSize: 13,
    color: '#64748B',
    lineHeight: 18,
  },
  actions: {
    width: '100%',
    gap: 12,
  },
  primaryButton: {
    backgroundColor: '#2563EB',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
  },
  primaryButtonText: {
    color: '#FFFFFF',
    fontSize: 15,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  secondaryButtonText: {
    color: '#334155',
    fontSize: 15,
    fontWeight: '600',
  },
  logoutButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  logoutButtonText: {
    color: '#EF4444',
    fontSize: 14,
    fontWeight: '600',
  },
});

export default WorkerAccountStatusScreen;
