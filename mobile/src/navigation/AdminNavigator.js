import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Text } from 'react-native';
import ROUTES from './routes';
import ScreenPlaceholder from '../screens/placeholder/ScreenPlaceholder';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

// --- Admin Screens Placeholders ---
const AdminOverviewScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Cooperative Admin Overview"
    subtitle="KPI Cards (Active workers, bookings, pending verifications) & Needs Attention triage"
    role="admin"
    navigation={navigation}
    actions={[
      { label: '🔍 Worker Verification Queue', route: ROUTES.ADMIN.VERIFICATION_QUEUE },
      { label: '⚖️ Fair Distribution & Utilisation (Flagship)', route: ROUTES.ADMIN.FAIR_DISTRIBUTION },
      { label: '📊 AI Demand Forecast & Analytics', route: ROUTES.ADMIN.ANALYTICS_FORECAST },
      { label: '🏥 Welfare Programmes Management', route: ROUTES.ADMIN.WELFARE_PROGRAMS },
    ]}
  />
);

const VerificationQueueScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Worker Verification Queue"
    subtitle="Pending worker applications waiting for certificate review & approval"
    role="admin"
    navigation={navigation}
    actions={[
      { label: 'Inspect Worker Certificate & OCR Detail', route: ROUTES.ADMIN.VERIFICATION_DETAIL },
    ]}
  />
);

const VerificationDetailScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Verification Detail & Certificate Viewer"
    subtitle="Worker profile, skills, zoomable trade certificate with backend OCR text/confidence"
    role="admin"
    navigation={navigation}
    actions={[
      { label: '✅ Approve Worker', onPress: () => navigation.goBack() },
      { label: '❌ Reject with Reason', onPress: () => navigation.goBack() },
      { label: '🔄 Request Re-upload', onPress: () => navigation.goBack() },
    ]}
  />
);

const WorkersDirectoryScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Workers Directory"
    subtitle="Search & filter by skill, status (verified/suspended), availability, cooperative"
    role="admin"
    navigation={navigation}
    actions={[
      { label: 'Open Worker Admin Detail', route: ROUTES.ADMIN.WORKER_DETAIL },
      { label: 'Go to Verification Queue', route: ROUTES.ADMIN.VERIFICATION_QUEUE },
    ]}
  />
);

const WorkerDetailAdminScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Worker Admin Detail"
    subtitle="Utilization stats, ratings, current weekly workload, Suspend/Reactivate actions"
    role="admin"
    navigation={navigation}
    actions={[
      { label: '⚠️ Suspend / Reactivate Worker', onPress: () => alert('Status toggled (Mock)') },
    ]}
  />
);

const BookingsMonitorScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Bookings Monitor"
    subtitle="Live status tracking, emergency bookings highlighted, filter by area/status"
    role="admin"
    navigation={navigation}
    actions={[
      { label: 'Inspect Booking Detail & Match Reason', route: ROUTES.ADMIN.BOOKING_DETAIL },
    ]}
  />
);

const BookingDetailAdminScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Booking Detail (Admin View)"
    subtitle="Full timeline, customer/worker details, AI match reason, manual reassign action"
    role="admin"
    navigation={navigation}
    actions={[
      { label: '🔄 Manual Reassign Worker (Mock)', onPress: () => alert('Reassigned (Mock)') },
    ]}
  />
);

const FairDistributionScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Fair Distribution & Utilisation (Flagship)"
    subtitle="Jobs-per-worker distribution, fairness score gauge, under-utilised & over-loaded alerts"
    role="admin"
    navigation={navigation}
    actions={[
      { label: 'View Demand Forecast', route: ROUTES.ADMIN.ANALYTICS_FORECAST },
    ]}
  />
);

const AdminComplaintsScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Complaints Management"
    subtitle="Status tabs: Open / In Review / Resolved. Triage escalated issues"
    role="admin"
    navigation={navigation}
    actions={[
      { label: 'Open Complaint Detail & Audit Trail', route: ROUTES.ADMIN.COMPLAINT_DETAIL },
    ]}
  />
);

const ComplaintDetailScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Complaint Resolution & Notes"
    subtitle="Parties involved, booking reference, resolution notes, Start Review / Resolve / Reject"
    role="admin"
    navigation={navigation}
    actions={[
      { label: 'Resolve Complaint', onPress: () => navigation.goBack() },
      { label: 'Reject Complaint', onPress: () => navigation.goBack() },
    ]}
  />
);

const AnalyticsForecastScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="AI Demand Forecast & Analytics"
    subtitle="7-day demand forecasting by skill category, revenue trends, service hot-spots"
    role="admin"
    navigation={navigation}
  />
);

const WelfareProgramsScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Welfare Programmes"
    subtitle="Insurance schemes, health checkups, skill training enrollment numbers"
    role="admin"
    navigation={navigation}
    actions={[
      { label: '➕ Create / Announce New Welfare Scheme', route: ROUTES.ADMIN.WELFARE_PROGRAM_CREATE },
    ]}
  />
);

const WelfareProgramCreateScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Create & Announce Welfare Scheme"
    subtitle="Set title, coverage, eligibility criteria, and broadcast to cooperative workers"
    role="admin"
    navigation={navigation}
    actions={[
      { label: 'Broadcast to Workers -> Save', onPress: () => navigation.goBack() },
    ]}
  />
);

const AdminMoreScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Administrator Tools & Settings"
    subtitle="Access flagship analytics, welfare schemes, and cooperative settings"
    role="admin"
    navigation={navigation}
    actions={[
      { label: '⚖️ Fair Distribution & Utilisation', route: ROUTES.ADMIN.FAIR_DISTRIBUTION },
      { label: '📈 Analytics & AI Demand Forecast', route: ROUTES.ADMIN.ANALYTICS_FORECAST },
      { label: '🏥 Welfare Programmes', route: ROUTES.ADMIN.WELFARE_PROGRAMS },
      { label: '⚙️ Admin Settings & Logout', route: ROUTES.ADMIN.SETTINGS },
    ]}
  />
);

const AdminSettingsScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Admin Settings"
    subtitle="Language, Audit Logs, Session details, Logout"
    role="admin"
    navigation={navigation}
  />
);

// --- Overview Stack ---
const AdminOverviewStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: '#F8FAFC' },
      headerTitleStyle: { color: '#0F172A', fontWeight: '600' },
    }}
  >
    <Stack.Screen
      name={ROUTES.ADMIN.OVERVIEW}
      component={AdminOverviewScreen}
      options={{ title: 'Admin Overview' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.VERIFICATION_QUEUE}
      component={VerificationQueueScreen}
      options={{ title: 'Pending Verifications' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.VERIFICATION_DETAIL}
      component={VerificationDetailScreen}
      options={{ title: 'Verification Details' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.FAIR_DISTRIBUTION}
      component={FairDistributionScreen}
      options={{ title: 'Fair Distribution' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.ANALYTICS_FORECAST}
      component={AnalyticsForecastScreen}
      options={{ title: 'Demand Forecast' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.WELFARE_PROGRAMS}
      component={WelfareProgramsScreen}
      options={{ title: 'Welfare Schemes' }}
    />
  </Stack.Navigator>
);

// --- Workers Stack ---
const AdminWorkersStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: '#F8FAFC' },
      headerTitleStyle: { color: '#0F172A', fontWeight: '600' },
    }}
  >
    <Stack.Screen
      name={ROUTES.ADMIN.WORKERS_DIRECTORY}
      component={WorkersDirectoryScreen}
      options={{ title: 'Workers Directory' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.WORKER_DETAIL}
      component={WorkerDetailAdminScreen}
      options={{ title: 'Worker Profile (Admin)' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.VERIFICATION_QUEUE}
      component={VerificationQueueScreen}
      options={{ title: 'Pending Verifications' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.VERIFICATION_DETAIL}
      component={VerificationDetailScreen}
      options={{ title: 'Verification Details' }}
    />
  </Stack.Navigator>
);

// --- Bookings Stack ---
const AdminBookingsStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: '#F8FAFC' },
      headerTitleStyle: { color: '#0F172A', fontWeight: '600' },
    }}
  >
    <Stack.Screen
      name={ROUTES.ADMIN.BOOKINGS_MONITOR}
      component={BookingsMonitorScreen}
      options={{ title: 'Bookings Monitor' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.BOOKING_DETAIL}
      component={BookingDetailAdminScreen}
      options={{ title: 'Booking Detail' }}
    />
  </Stack.Navigator>
);

// --- Complaints Stack ---
const AdminComplaintsStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: '#F8FAFC' },
      headerTitleStyle: { color: '#0F172A', fontWeight: '600' },
    }}
  >
    <Stack.Screen
      name={ROUTES.ADMIN.COMPLAINTS}
      component={AdminComplaintsScreen}
      options={{ title: 'Complaints' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.COMPLAINT_DETAIL}
      component={ComplaintDetailScreen}
      options={{ title: 'Complaint Detail' }}
    />
  </Stack.Navigator>
);

// --- More Stack ---
const AdminMoreStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: '#F8FAFC' },
      headerTitleStyle: { color: '#0F172A', fontWeight: '600' },
    }}
  >
    <Stack.Screen
      name={ROUTES.ADMIN.MORE_TAB}
      component={AdminMoreScreen}
      options={{ title: 'Cooperative Management' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.FAIR_DISTRIBUTION}
      component={FairDistributionScreen}
      options={{ title: 'Fair Distribution' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.ANALYTICS_FORECAST}
      component={AnalyticsForecastScreen}
      options={{ title: 'AI Demand Forecast' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.WELFARE_PROGRAMS}
      component={WelfareProgramsScreen}
      options={{ title: 'Welfare Programmes' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.WELFARE_PROGRAM_CREATE}
      component={WelfareProgramCreateScreen}
      options={{ title: 'New Welfare Scheme' }}
    />
    <Stack.Screen
      name={ROUTES.ADMIN.SETTINGS}
      component={AdminSettingsScreen}
      options={{ title: 'Admin Settings' }}
    />
  </Stack.Navigator>
);

export const AdminNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: '#D97706', // Cooperative Amber for Admin
        tabBarInactiveTintColor: '#64748B',
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopColor: '#E2E8F0',
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarLabel: ({ focused, color }) => {
          let label = 'Overview';
          if (route.name === ROUTES.ADMIN.WORKERS_TAB) label = 'Workers';
          if (route.name === ROUTES.ADMIN.BOOKINGS_TAB) label = 'Bookings';
          if (route.name === ROUTES.ADMIN.COMPLAINTS_TAB) label = 'Complaints';
          if (route.name === ROUTES.ADMIN.MORE_TAB) label = 'More';
          return (
            <Text style={{ fontSize: 11, fontWeight: focused ? '700' : '500', color }}>
              {label}
            </Text>
          );
        },
        tabBarIcon: ({ focused, color }) => {
          let icon = '📊';
          if (route.name === ROUTES.ADMIN.WORKERS_TAB) icon = '👥';
          if (route.name === ROUTES.ADMIN.BOOKINGS_TAB) icon = '📋';
          if (route.name === ROUTES.ADMIN.COMPLAINTS_TAB) icon = '⚠️';
          if (route.name === ROUTES.ADMIN.MORE_TAB) icon = '⚙️';
          return <Text style={{ fontSize: 18 }}>{icon}</Text>;
        },
      })}
    >
      <Tab.Screen name={ROUTES.ADMIN.OVERVIEW_TAB} component={AdminOverviewStack} />
      <Tab.Screen name={ROUTES.ADMIN.WORKERS_TAB} component={AdminWorkersStack} />
      <Tab.Screen name={ROUTES.ADMIN.BOOKINGS_TAB} component={AdminBookingsStack} />
      <Tab.Screen name={ROUTES.ADMIN.COMPLAINTS_TAB} component={AdminComplaintsStack} />
      <Tab.Screen name={ROUTES.ADMIN.MORE_TAB} component={AdminMoreStack} />
    </Tab.Navigator>
  );
};

export default AdminNavigator;
