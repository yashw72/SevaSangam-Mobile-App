import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../../context/AuthContext';

export const RoleSelectScreen = ({ route }) => {
  const { t } = useTranslation();
  const { login } = useAuth();
  const phone = route.params?.phone || '+91 9876543210';

  const [selectedRole, setSelectedRole] = useState('customer'); // 'customer' | 'worker'

  const handleContinue = async () => {
    if (selectedRole === 'customer') {
      await login({
        role: 'customer',
        name: 'New Customer',
        phone,
      });
    } else if (selectedRole === 'worker') {
      // New self-registered worker starts with verified/active mock session
      await login({
        role: 'worker',
        status: 'verified',
        name: 'New Cooperative Worker',
        phone,
      });
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <Text style={styles.title}>{t('auth:role_select_title')}</Text>
          <Text style={styles.subtitle}>{t('auth:role_select_subtitle')}</Text>
        </View>

        <View style={styles.rolesContainer}>
          {/* Customer Option */}
          <TouchableOpacity
            style={[
              styles.roleCard,
              selectedRole === 'customer' && styles.roleCardActiveCustomer,
            ]}
            onPress={() => setSelectedRole('customer')}
            activeOpacity={0.7}
          >
            <View style={styles.cardTopRow}>
              <View style={[styles.roleIconBadge, styles.customerIconBadge]}>
                <Text style={styles.roleIcon}>👤</Text>
              </View>
              <View style={[styles.radioCircle, selectedRole === 'customer' && styles.radioCircleActive]}>
                {selectedRole === 'customer' && <View style={styles.radioDot} />}
              </View>
            </View>

            <Text style={styles.roleTitle}>{t('auth:role_customer_title')}</Text>
            <Text style={styles.roleDesc}>{t('auth:role_customer_desc')}</Text>

            <View style={styles.featurePills}>
              <View style={styles.pill}><Text style={styles.pillText}>⚡ 1-Tap SOS</Text></View>
              <View style={styles.pill}><Text style={styles.pillText}>🛡️ Verified Pros</Text></View>
              <View style={styles.pill}><Text style={styles.pillText}>⚖️ Fair Pricing</Text></View>
            </View>
          </TouchableOpacity>

          {/* Worker Option */}
          <TouchableOpacity
            style={[
              styles.roleCard,
              selectedRole === 'worker' && styles.roleCardActiveWorker,
            ]}
            onPress={() => setSelectedRole('worker')}
            activeOpacity={0.7}
          >
            <View style={styles.cardTopRow}>
              <View style={[styles.roleIconBadge, styles.workerIconBadge]}>
                <Text style={styles.roleIcon}>🛠️</Text>
              </View>
              <View style={[styles.radioCircle, selectedRole === 'worker' && styles.radioCircleActiveWorker]}>
                {selectedRole === 'worker' && <View style={[styles.radioDot, styles.radioDotWorker]} />}
              </View>
            </View>

            <Text style={styles.roleTitle}>{t('auth:role_worker_title')}</Text>
            <Text style={styles.roleDesc}>{t('auth:role_worker_desc')}</Text>

            <View style={styles.featurePills}>
              <View style={styles.pill}><Text style={styles.pillText}>🤝 Cooperative Member</Text></View>
              <View style={styles.pill}><Text style={styles.pillText}>📈 Fair Job Share</Text></View>
              <View style={styles.pill}><Text style={styles.pillText}>🏥 Welfare & Insurance</Text></View>
            </View>
          </TouchableOpacity>
        </View>

        <View style={styles.infoBanner}>
          <Text style={styles.infoIcon}>🔒</Text>
          <Text style={styles.infoText}>
            Cooperative Administrator accounts are pre-provisioned by the cooperative society and cannot self-register.
          </Text>
        </View>
      </ScrollView>

      <View style={styles.bottomBar}>
        <TouchableOpacity
          style={[styles.continueButton, selectedRole === 'worker' && styles.continueButtonWorker]}
          onPress={handleContinue}
          activeOpacity={0.8}
        >
          <Text style={styles.continueButtonText}>
            {selectedRole === 'customer'
              ? t('auth:continue_as_customer')
              : t('auth:continue_as_worker')}
          </Text>
          <Text style={styles.continueArrow}>→</Text>
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
    paddingBottom: 110,
  },
  header: {
    marginTop: 12,
    marginBottom: 28,
  },
  title: {
    fontSize: 24,
    fontWeight: '800',
    color: '#0F172A',
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
    lineHeight: 20,
  },
  rolesContainer: {
    gap: 16,
    marginBottom: 24,
  },
  roleCard: {
    backgroundColor: '#F8FAFC',
    borderRadius: 20,
    padding: 20,
    borderWidth: 2,
    borderColor: '#E2E8F0',
  },
  roleCardActiveCustomer: {
    borderColor: '#2563EB',
    backgroundColor: '#EFF6FF',
  },
  roleCardActiveWorker: {
    borderColor: '#059669',
    backgroundColor: '#ECFDF5',
  },
  cardTopRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 14,
  },
  roleIconBadge: {
    width: 48,
    height: 48,
    borderRadius: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  customerIconBadge: {
    backgroundColor: '#DBEAFE',
  },
  workerIconBadge: {
    backgroundColor: '#D1FAE5',
  },
  roleIcon: {
    fontSize: 24,
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
  radioCircleActiveWorker: {
    borderColor: '#059669',
  },
  radioDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#2563EB',
  },
  radioDotWorker: {
    backgroundColor: '#059669',
  },
  roleTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 6,
  },
  roleDesc: {
    fontSize: 13,
    color: '#475569',
    lineHeight: 18,
    marginBottom: 16,
  },
  featurePills: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
  },
  pill: {
    backgroundColor: '#FFFFFF',
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#CBD5E1',
  },
  pillText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#334155',
  },
  infoBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#F1F5F9',
    padding: 14,
    borderRadius: 12,
    gap: 10,
  },
  infoIcon: {
    fontSize: 16,
  },
  infoText: {
    flex: 1,
    fontSize: 12,
    color: '#64748B',
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
  continueButtonWorker: {
    backgroundColor: '#059669',
    shadowColor: '#059669',
  },
  continueButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '700',
  },
  continueArrow: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: '700',
  },
});

export default RoleSelectScreen;
