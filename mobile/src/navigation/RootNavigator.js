import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AuthNavigator from './AuthNavigator';
import CustomerNavigator from './CustomerNavigator';
import WorkerNavigator from './WorkerNavigator';
import AdminNavigator from './AdminNavigator';
import WorkerAccountStatusScreen from '../screens/auth/WorkerAccountStatus';

/**
 * Stubbed Auth State Hook for Phase 1 Navigation Shell Testing.
 * In Prompt 4, this will be wired to context/AuthContext.js.
 */
export const useAuthStub = () => {
  // Test role state: 'customer' | 'worker_verified' | 'worker_pending' | 'worker_suspended' | 'admin' | 'unauthenticated'
  const [testAuthState, setTestAuthState] = useState({
    isAuthenticated: true,
    role: 'customer', // Default for testing: customer
    workerVerificationStatus: 'verified',
  });

  return {
    ...testAuthState,
    setRole: (roleKey) => {
      switch (roleKey) {
        case 'customer':
          setTestAuthState({ isAuthenticated: true, role: 'customer', workerVerificationStatus: 'verified' });
          break;
        case 'worker_verified':
          setTestAuthState({ isAuthenticated: true, role: 'worker', workerVerificationStatus: 'verified' });
          break;
        case 'worker_pending':
          setTestAuthState({ isAuthenticated: true, role: 'worker', workerVerificationStatus: 'pending' });
          break;
        case 'worker_suspended':
          setTestAuthState({ isAuthenticated: true, role: 'worker', workerVerificationStatus: 'suspended' });
          break;
        case 'admin':
          setTestAuthState({ isAuthenticated: true, role: 'admin', workerVerificationStatus: 'verified' });
          break;
        case 'unauthenticated':
        default:
          setTestAuthState({ isAuthenticated: false, role: null, workerVerificationStatus: 'pending' });
          break;
      }
    },
  };
};

export const RootNavigator = ({ authOverride }) => {
  const auth = authOverride || useAuthStub();
  const { isAuthenticated, role, workerVerificationStatus, setRole } = auth;

  // Decide which navigator to render based on authentication & role guards
  const renderActiveNavigator = () => {
    if (!isAuthenticated || !role) {
      return <AuthNavigator />;
    }

    if (role === 'customer') {
      return <CustomerNavigator />;
    }

    if (role === 'worker') {
      if (workerVerificationStatus === 'verified') {
        return <WorkerNavigator />;
      }
      return (
        <WorkerAccountStatusScreen
          status={workerVerificationStatus}
          reason={
            workerVerificationStatus === 'pending'
              ? 'Your electrician certification is being verified by the Cooperative Administrator.'
              : 'Your account is suspended due to a pending verification audit.'
          }
          onLogout={() => setRole?.('unauthenticated')}
        />
      );
    }

    if (role === 'admin') {
      return <AdminNavigator />;
    }

    return <AuthNavigator />;
  };

  return (
    <View style={styles.rootContainer}>
      {renderActiveNavigator()}

      {/* Dev / Test Role Switcher Bar to verify all navigators end-to-end */}
      <SafeAreaView edges={['bottom']} style={styles.devBarContainer}>
        <View style={styles.devBarHeader}>
          <Text style={styles.devBarTitle}>
            Role Switcher: <Text style={styles.devBarActiveRole}>{role || 'Auth'} ({workerVerificationStatus})</Text>
          </Text>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.devBarScroll}>
          <TouchableOpacity
            style={[styles.devButton, role === 'customer' && styles.devButtonActive]}
            onPress={() => setRole?.('customer')}
          >
            <Text style={[styles.devButtonText, role === 'customer' && styles.devButtonTextActive]}>
              👤 Customer
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.devButton, role === 'worker' && workerVerificationStatus === 'verified' && styles.devButtonActive]}
            onPress={() => setRole?.('worker_verified')}
          >
            <Text style={[styles.devButtonText, role === 'worker' && workerVerificationStatus === 'verified' && styles.devButtonTextActive]}>
              🛠️ Worker (Verified)
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.devButton, role === 'worker' && workerVerificationStatus === 'pending' && styles.devButtonActive]}
            onPress={() => setRole?.('worker_pending')}
          >
            <Text style={[styles.devButtonText, role === 'worker' && workerVerificationStatus === 'pending' && styles.devButtonTextActive]}>
              ⏳ Worker (Pending)
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.devButton, role === 'admin' && styles.devButtonActive]}
            onPress={() => setRole?.('admin')}
          >
            <Text style={[styles.devButtonText, role === 'admin' && styles.devButtonTextActive]}>
              📊 Admin
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.devButton, !isAuthenticated && styles.devButtonActive]}
            onPress={() => setRole?.('unauthenticated')}
          >
            <Text style={[styles.devButtonText, !isAuthenticated && styles.devButtonTextActive]}>
              🔒 Auth Flow
            </Text>
          </TouchableOpacity>
        </ScrollView>
      </SafeAreaView>
    </View>
  );
};

const styles = StyleSheet.create({
  rootContainer: {
    flex: 1,
  },
  devBarContainer: {
    backgroundColor: '#1E293B',
    borderTopWidth: 1,
    borderTopColor: '#334155',
    paddingVertical: 6,
  },
  devBarHeader: {
    paddingHorizontal: 12,
    marginBottom: 4,
  },
  devBarTitle: {
    fontSize: 10,
    color: '#94A3B8',
    fontWeight: '600',
    textTransform: 'uppercase',
  },
  devBarActiveRole: {
    color: '#38BDF8',
    fontWeight: '700',
  },
  devBarScroll: {
    paddingHorizontal: 10,
    gap: 6,
  },
  devButton: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    backgroundColor: '#334155',
    borderRadius: 6,
  },
  devButtonActive: {
    backgroundColor: '#0284C7',
  },
  devButtonText: {
    fontSize: 11,
    color: '#E2E8F0',
    fontWeight: '500',
  },
  devButtonTextActive: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
});

export default RootNavigator;
