import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Text } from 'react-native';
import ROUTES from './routes';
import ScreenPlaceholder from '../screens/placeholder/ScreenPlaceholder';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

// --- Worker Screens Placeholders ---
const WorkerHomeScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Worker Dashboard"
    subtitle="Online/Offline Toggle, Fair-share workload meter, Active job card"
    role="worker"
    navigation={navigation}
    actions={[
      { label: '🔔 View New Job Requests (Accept/Reject)', route: ROUTES.WORKER.JOB_REQUESTS },
      { label: '🚀 Open Active Job Screen', route: ROUTES.WORKER.ACTIVE_JOB },
      { label: '🛡️ View My Welfare & Insurance Card', route: ROUTES.WORKER.WELFARE_CARD },
    ]}
  />
);

const JobRequestsScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Incoming Job Requests"
    subtitle="Service, Distance, Area, Payout, Emergency badge, Accept/Reject timer"
    role="worker"
    navigation={navigation}
    actions={[
      { label: 'Accept Job -> Go to Active Job', route: ROUTES.WORKER.ACTIVE_JOB },
      { label: 'Reject Job with Reason', onPress: () => navigation.goBack() },
    ]}
  />
);

const ActiveJobScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Active Job in Progress"
    subtitle="Steps: On the way -> Started -> Completed. Navigation link & Call button"
    role="worker"
    navigation={navigation}
    actions={[
      { label: 'Mark Completed -> View Earnings', route: ROUTES.WORKER.EARNINGS },
      { label: 'Back to Worker Home', route: ROUTES.WORKER.HOME },
    ]}
  />
);

const WorkerJobsScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Job History"
    subtitle="Completed and past jobs list with payment and cooperative details"
    role="worker"
    navigation={navigation}
    actions={[
      { label: 'Open Active Job', route: ROUTES.WORKER.ACTIVE_JOB },
      { label: 'View Customer Reviews', route: ROUTES.WORKER.REVIEWS },
    ]}
  />
);

const WorkerEarningsScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Earnings & Payouts"
    subtitle="Day / Week / Month totals, per-job breakdown, Cash/UPI status"
    role="worker"
    navigation={navigation}
    actions={[
      { label: 'View Past Completed Jobs', route: ROUTES.WORKER.JOB_HISTORY },
    ]}
  />
);

const WorkerReviewsScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Customer Ratings & Reviews"
    subtitle="Average star rating, review tags, feedback comments"
    role="worker"
    navigation={navigation}
  />
);

const WorkerProfileScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Worker Profile"
    subtitle="Skills, Cooperative Membership, Experience, Verification Status"
    role="worker"
    navigation={navigation}
    actions={[
      { label: 'Edit Skills & Experience', route: ROUTES.WORKER.SKILLS_EDIT },
      { label: 'Manage & Upload Certificates', route: ROUTES.WORKER.CERTIFICATES },
      { label: 'View Welfare & Insurance Card', route: ROUTES.WORKER.WELFARE_CARD },
      { label: 'Worker Settings', route: ROUTES.WORKER.SETTINGS },
    ]}
  />
);

const WorkerSkillsEditScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Edit Skills & Service Radius"
    subtitle="Primary skill selection, years of experience, service area radius"
    role="worker"
    navigation={navigation}
  />
);

const WorkerCertificatesScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Certificates & Verification"
    subtitle="Upload trade certificates, ID documents for Cooperative Admin review"
    role="worker"
    navigation={navigation}
  />
);

const WorkerWelfareCardScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Welfare & Insurance Card"
    subtitle="Cooperative Name, Member ID, Group Insurance coverage & schemes"
    role="worker"
    navigation={navigation}
  />
);

const WorkerSettingsScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Worker Settings"
    subtitle="Language preferences, Notifications, Support & Logout"
    role="worker"
    navigation={navigation}
    actions={[
      { label: 'Help & Cooperative Support', route: ROUTES.WORKER.HELP },
    ]}
  />
);

const WorkerHelpScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Worker Support & Help"
    subtitle="Contact cooperative manager, emergency contact, FAQs"
    role="worker"
    navigation={navigation}
  />
);

// --- Home Stack ---
const WorkerHomeStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: '#F8FAFC' },
      headerTitleStyle: { color: '#0F172A', fontWeight: '600' },
    }}
  >
    <Stack.Screen
      name={ROUTES.WORKER.HOME}
      component={WorkerHomeScreen}
      options={{ title: 'Worker Home' }}
    />
    <Stack.Screen
      name={ROUTES.WORKER.JOB_REQUESTS}
      component={JobRequestsScreen}
      options={{ title: 'Job Requests' }}
    />
    <Stack.Screen
      name={ROUTES.WORKER.ACTIVE_JOB}
      component={ActiveJobScreen}
      options={{ title: 'Active Job' }}
    />
    <Stack.Screen
      name={ROUTES.WORKER.WELFARE_CARD}
      component={WorkerWelfareCardScreen}
      options={{ title: 'Welfare & Insurance' }}
    />
  </Stack.Navigator>
);

// --- Jobs Stack ---
const WorkerJobsStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: '#F8FAFC' },
      headerTitleStyle: { color: '#0F172A', fontWeight: '600' },
    }}
  >
    <Stack.Screen
      name={ROUTES.WORKER.JOB_HISTORY}
      component={WorkerJobsScreen}
      options={{ title: 'Job History' }}
    />
    <Stack.Screen
      name={ROUTES.WORKER.ACTIVE_JOB}
      component={ActiveJobScreen}
      options={{ title: 'Active Job' }}
    />
    <Stack.Screen
      name={ROUTES.WORKER.REVIEWS}
      component={WorkerReviewsScreen}
      options={{ title: 'Customer Reviews' }}
    />
  </Stack.Navigator>
);

// --- Profile Stack ---
const WorkerProfileStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: '#F8FAFC' },
      headerTitleStyle: { color: '#0F172A', fontWeight: '600' },
    }}
  >
    <Stack.Screen
      name={ROUTES.WORKER.PROFILE}
      component={WorkerProfileScreen}
      options={{ title: 'Worker Profile' }}
    />
    <Stack.Screen
      name={ROUTES.WORKER.SKILLS_EDIT}
      component={WorkerSkillsEditScreen}
      options={{ title: 'Edit Skills' }}
    />
    <Stack.Screen
      name={ROUTES.WORKER.CERTIFICATES}
      component={WorkerCertificatesScreen}
      options={{ title: 'Trade Certificates' }}
    />
    <Stack.Screen
      name={ROUTES.WORKER.WELFARE_CARD}
      component={WorkerWelfareCardScreen}
      options={{ title: 'Welfare Card' }}
    />
    <Stack.Screen
      name={ROUTES.WORKER.SETTINGS}
      component={WorkerSettingsScreen}
      options={{ title: 'Settings' }}
    />
    <Stack.Screen
      name={ROUTES.WORKER.HELP}
      component={WorkerHelpScreen}
      options={{ title: 'Help & Support' }}
    />
  </Stack.Navigator>
);

export const WorkerNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: '#059669', // Emerald Green for Worker
        tabBarInactiveTintColor: '#64748B',
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopColor: '#E2E8F0',
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
        tabBarLabel: ({ focused, color }) => {
          let label = 'Home';
          if (route.name === ROUTES.WORKER.JOBS_TAB) label = 'Jobs';
          if (route.name === ROUTES.WORKER.EARNINGS_TAB) label = 'Earnings';
          if (route.name === ROUTES.WORKER.PROFILE_TAB) label = 'Profile';
          return (
            <Text style={{ fontSize: 11, fontWeight: focused ? '700' : '500', color }}>
              {label}
            </Text>
          );
        },
        tabBarIcon: ({ focused, color }) => {
          let icon = '🛠️';
          if (route.name === ROUTES.WORKER.JOBS_TAB) icon = '📋';
          if (route.name === ROUTES.WORKER.EARNINGS_TAB) icon = '💰';
          if (route.name === ROUTES.WORKER.PROFILE_TAB) icon = '👤';
          return <Text style={{ fontSize: 18 }}>{icon}</Text>;
        },
      })}
    >
      <Tab.Screen name={ROUTES.WORKER.HOME_TAB} component={WorkerHomeStack} />
      <Tab.Screen name={ROUTES.WORKER.JOBS_TAB} component={WorkerJobsStack} />
      <Tab.Screen
        name={ROUTES.WORKER.EARNINGS_TAB}
        component={WorkerEarningsScreen}
        options={{ headerShown: true, title: 'My Earnings' }}
      />
      <Tab.Screen name={ROUTES.WORKER.PROFILE_TAB} component={WorkerProfileStack} />
    </Tab.Navigator>
  );
};

export default WorkerNavigator;
