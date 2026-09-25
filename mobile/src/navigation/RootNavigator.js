import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { useAuth } from '../context/AuthContext';
import AuthNavigator from './AuthNavigator';
import CustomerNavigator from './CustomerNavigator';
import WorkerNavigator from './WorkerNavigator';
import AdminNavigator from './AdminNavigator';
import WorkerAccountStatusScreen from '../screens/auth/WorkerAccountStatus';
import ROUTES from './routes';

/**
 * Minimal stack navigator for the WorkerAccountStatus screen.
 * Gives it a `navigation` prop so the "Edit Profile" and "Re-upload Certificates"
 * buttons can navigate to stub screens (Priti builds the real ones later).
 */
const StatusStack = createNativeStackNavigator();

const WorkerAccountStatusNavigator = () => {
  // Stub placeholder for screens that don't exist yet
  const StubScreen = ({ route }) => (
    <SafeAreaView style={styles.stubContainer}>
      <Text style={styles.stubIcon}>🚧</Text>
      <Text style={styles.stubTitle}>{route.name}</Text>
      <Text style={styles.stubSubtitle}>This screen will be built by Priti.</Text>
    </SafeAreaView>
  );

  return (
    <StatusStack.Navigator screenOptions={{ headerShown: false }}>
      <StatusStack.Screen
        name={ROUTES.AUTH.WORKER_ACCOUNT_STATUS}
        component={WorkerAccountStatusScreen}
      />
      {/* Stub navigation targets — Priti builds these real screens later */}
      <StatusStack.Screen
        name={ROUTES.WORKER.PROFILE}
        component={StubScreen}
        options={{ headerShown: true, title: 'Edit Profile' }}
      />
      <StatusStack.Screen
        name={ROUTES.WORKER.CERTIFICATES}
        component={StubScreen}
        options={{ headerShown: true, title: 'Certificates' }}
      />
    </StatusStack.Navigator>
  );
};

export const RootNavigator = () => {
  const { user, role, token, status, isLoading, login, logout } = useAuth();

  // 1. Show loading state while session is being restored from secure storage
  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2563EB" />
        <Text style={styles.loadingText}>Restoring session...</Text>
      </View>
    );
  }

  // 2. Decide active navigator based on real AuthContext state & route guards
  const renderActiveNavigator = () => {
    // If not authenticated or no token, send to Auth flow
    if (!token || !role) {
      return <AuthNavigator />;
    }

    // Role guard: Customer
    if (role === 'customer') {
      return <CustomerNavigator />;
    }

    // Role guard: Worker — ONLY verified workers reach WorkerNavigator
    if (role === 'worker') {
      if (status === 'verified') {
        return <WorkerNavigator />;
      }
      // pending / rejected / suspended → WorkerAccountStatus (never WorkerNavigator)
      return <WorkerAccountStatusNavigator />;
    }

    // Role guard: Admin
    if (role === 'admin') {
      return <AdminNavigator />;
    }

    // Fallback
    return <AuthNavigator />;
  };

  return (
    <View style={styles.rootContainer}>
      {renderActiveNavigator()}

      {/* Dev / Demo Role Switcher Bar: Directly invokes real AuthContext.login / logout */}
      <SafeAreaView edges={['bottom']} style={styles.devBarContainer}>
        <View style={styles.devBarHeader}>
          <Text style={styles.devBarTitle}>
            Active Session: <Text style={styles.devBarActiveRole}>{role ? `${role.toUpperCase()} (${status || 'active'})` : 'UNAUTHENTICATED'}</Text>
          </Text>
        </View>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.devBarScroll}>
          <TouchableOpacity
            style={[styles.devButton, role === 'customer' && styles.devButtonActive]}
            onPress={() => login({ role: 'customer', name: 'Pooja Sharma (Customer)' })}
          >
            <Text style={[styles.devButtonText, role === 'customer' && styles.devButtonTextActive]}>
              👤 Customer
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.devButton, role === 'worker' && status === 'verified' && styles.devButtonActive]}
            onPress={() => login({ role: 'worker', status: 'verified', name: 'Ramesh Kumar (Worker)' })}
          >
            <Text style={[styles.devButtonText, role === 'worker' && status === 'verified' && styles.devButtonTextActive]}>
              🛠️ Worker (Verified)
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.devButton, role === 'worker' && status === 'pending' && styles.devButtonActive]}
            onPress={() => login({ role: 'worker', status: 'pending', name: 'Suresh Patil (Pending)' })}
          >
            <Text style={[styles.devButtonText, role === 'worker' && status === 'pending' && styles.devButtonTextActive]}>
              ⏳ Worker (Pending)
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.devButton, role === 'worker' && status === 'rejected' && styles.devButtonActive]}
            onPress={() => login({ role: 'worker', status: 'rejected', name: 'Amit Joshi (Rejected)' })}
          >
            <Text style={[styles.devButtonText, role === 'worker' && status === 'rejected' && styles.devButtonTextActive]}>
              ❌ Worker (Rejected)
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.devButton, role === 'worker' && status === 'suspended' && styles.devButtonActive]}
            onPress={() => login({ role: 'worker', status: 'suspended', name: 'Vijay Shinde (Suspended)' })}
          >
            <Text style={[styles.devButtonText, role === 'worker' && status === 'suspended' && styles.devButtonTextActive]}>
              ⚠️ Worker (Suspended)
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.devButton, role === 'admin' && styles.devButtonActive]}
            onPress={() => login({ role: 'admin', status: 'verified', name: 'Coop Admin' })}
          >
            <Text style={[styles.devButtonText, role === 'admin' && styles.devButtonTextActive]}>
              📊 Admin (15m expiry)
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.devButton, !token && styles.devButtonActive]}
            onPress={logout}
          >
            <Text style={[styles.devButtonText, !token && styles.devButtonTextActive]}>
              🔒 Logout / Auth
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
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F8FAFC',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 14,
    color: '#64748B',
    fontWeight: '500',
  },
  // Stub screen styles for placeholder screens
  stubContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#F8FAFC',
    padding: 24,
  },
  stubIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  stubTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 8,
  },
  stubSubtitle: {
    fontSize: 14,
    color: '#64748B',
    textAlign: 'center',
  },
  // Dev bar styles
  devBarContainer: {
    backgroundColor: '#0F172A',
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
    paddingVertical: 5,
    paddingHorizontal: 10,
    backgroundColor: '#1E293B',
    borderRadius: 6,
    borderWidth: 1,
    borderColor: '#334155',
  },
  devButtonActive: {
    backgroundColor: '#0284C7',
    borderColor: '#38BDF8',
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

