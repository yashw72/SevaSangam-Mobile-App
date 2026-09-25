import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

export const ScreenPlaceholder = ({
  title,
  subtitle,
  role = 'General',
  actions = [],
  navigation,
}) => {
  return (
    <SafeAreaView style={styles.safeArea} edges={['top', 'left', 'right']}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.badgeContainer}>
          <View style={[styles.badge, { backgroundColor: getRoleColor(role) }]}>
            <Text style={styles.badgeText}>{role.toUpperCase()}</Text>
          </View>
        </View>

        <Text style={styles.title}>{title}</Text>
        {subtitle ? <Text style={styles.subtitle}>{subtitle}</Text> : null}

        <View style={styles.card}>
          <Text style={styles.cardHeader}>Shell Placeholder Screen</Text>
          <Text style={styles.cardBody}>
            This is a functional navigation shell for <Text style={styles.bold}>{title}</Text>.
            Feature implementation will replace this shell.
          </Text>
        </View>

        {actions && actions.length > 0 && (
          <View style={styles.actionsSection}>
            <Text style={styles.actionsTitle}>Test Navigation Actions</Text>
            {actions.map((action, index) => (
              <TouchableOpacity
                key={index}
                style={styles.actionButton}
                activeOpacity={0.7}
                onPress={() => {
                  if (typeof action.onPress === 'function') {
                    action.onPress();
                  } else if (action.route && navigation) {
                    navigation.navigate(action.route, action.params);
                  }
                }}
              >
                <Text style={styles.actionButtonText}>
                  {action.label || `Go to ${action.route}`}
                </Text>
                <Text style={styles.actionArrow}>→</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const getRoleColor = (role) => {
  switch (role.toLowerCase()) {
    case 'customer':
      return '#2563EB'; // Blue
    case 'worker':
      return '#059669'; // Green
    case 'admin':
      return '#D97706'; // Amber / Cooperative Orange
    case 'auth':
      return '#7C3AED'; // Purple
    default:
      return '#4B5563';
  }
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F8FAFC',
  },
  container: {
    padding: 20,
    paddingBottom: 40,
  },
  badgeContainer: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  badge: {
    paddingVertical: 4,
    paddingHorizontal: 10,
    borderRadius: 6,
  },
  badgeText: {
    color: '#FFFFFF',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#0F172A',
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: '#64748B',
    marginBottom: 16,
  },
  card: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 20,
  },
  cardHeader: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1E293B',
    marginBottom: 6,
  },
  cardBody: {
    fontSize: 14,
    color: '#64748B',
    lineHeight: 20,
  },
  bold: {
    fontWeight: '600',
    color: '#0F172A',
  },
  actionsSection: {
    marginTop: 4,
  },
  actionsTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 10,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#FFFFFF',
    borderRadius: 10,
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: '#E2E8F0',
    marginBottom: 10,
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#1E293B',
  },
  actionArrow: {
    fontSize: 16,
    color: '#94A3B8',
    fontWeight: '600',
  },
});

export default ScreenPlaceholder;
