import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Text } from 'react-native';
import ROUTES from './routes';
import ScreenPlaceholder from '../screens/placeholder/ScreenPlaceholder';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

// --- Customer Screens Placeholders ---
const CustomerHomeScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Customer Home"
    subtitle="Categories grid, Emergency SOS CTA, Nearby verified workers"
    role="customer"
    navigation={navigation}
    actions={[
      { label: '🚨 Trigger Emergency Booking (≤ 2 taps)', route: ROUTES.CUSTOMER.EMERGENCY_BOOKING },
      { label: 'Browse Workers (Worker List)', route: ROUTES.CUSTOMER.WORKER_LIST },
      { label: 'View Worker Profile', route: ROUTES.CUSTOMER.WORKER_PROFILE },
      { label: 'Start New Booking Flow', route: ROUTES.CUSTOMER.BOOKING_FLOW },
    ]}
  />
);

const WorkerListScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Worker List & Category"
    subtitle="Filters, Best Match badge with fair-share reasoning"
    role="customer"
    navigation={navigation}
    actions={[
      { label: 'View Selected Worker Profile', route: ROUTES.CUSTOMER.WORKER_PROFILE },
      { label: 'Book Worker Now', route: ROUTES.CUSTOMER.BOOKING_FLOW },
    ]}
  />
);

const WorkerProfileScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Worker Profile"
    subtitle="Skills, Cooperative badge, Insurance/Welfare status, Ratings"
    role="customer"
    navigation={navigation}
    actions={[
      { label: 'Book This Worker', route: ROUTES.CUSTOMER.BOOKING_FLOW },
      { label: 'Back to Worker List', route: ROUTES.CUSTOMER.WORKER_LIST },
    ]}
  />
);

const BookingFlowScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Booking Flow"
    subtitle="Multi-step: Service -> Address -> Schedule -> Notes -> Estimate"
    role="customer"
    navigation={navigation}
    actions={[
      { label: 'Confirm Booking -> Go to Tracking', route: ROUTES.CUSTOMER.BOOKING_TRACKING },
      { label: 'Cancel Booking Flow', onPress: () => navigation.goBack() },
    ]}
  />
);

const EmergencyBookingScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Emergency Booking (1-Tap)"
    subtitle="Auto-detect location -> Instant nearby cooperative worker dispatch"
    role="customer"
    navigation={navigation}
    actions={[
      { label: 'Dispatch Worker -> Track Live', route: ROUTES.CUSTOMER.BOOKING_TRACKING },
      { label: 'Cancel Request', onPress: () => navigation.goBack() },
    ]}
  />
);

const BookingTrackingScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Live Booking Tracking"
    subtitle="Timeline (En route -> In progress -> Completed), live map ETA"
    role="customer"
    navigation={navigation}
    actions={[
      { label: 'View Full Booking Details', route: ROUTES.CUSTOMER.BOOKING_DETAIL },
      { label: 'Mark Job Completed -> Leave Review', route: ROUTES.CUSTOMER.RATE_REVIEW },
    ]}
  />
);

const CustomerBookingsScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="My Bookings"
    subtitle="Tabs: Upcoming / Completed / Cancelled"
    role="customer"
    navigation={navigation}
    actions={[
      { label: 'Track Active Booking', route: ROUTES.CUSTOMER.BOOKING_TRACKING },
      { label: 'View Booking Details', route: ROUTES.CUSTOMER.BOOKING_DETAIL },
      { label: 'Rate Completed Service', route: ROUTES.CUSTOMER.RATE_REVIEW },
    ]}
  />
);

const BookingDetailScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Booking Details"
    subtitle="Price estimate, cooperative details, worker info, status timeline"
    role="customer"
    navigation={navigation}
    actions={[
      { label: 'Track Live Status', route: ROUTES.CUSTOMER.BOOKING_TRACKING },
      { label: 'Need Help / Raise Complaint', route: ROUTES.CUSTOMER.HELP_COMPLAINT },
    ]}
  />
);

const RateReviewScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Rate & Review Service"
    subtitle="Star rating, tags, comment, cooperative worker feedback"
    role="customer"
    navigation={navigation}
    actions={[
      { label: 'Submit Review -> Back to Home', route: ROUTES.CUSTOMER.HOME },
    ]}
  />
);

const CustomerNotificationsScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Customer Notifications"
    subtitle="Booking updates, worker en route alerts, promotional offers"
    role="customer"
    navigation={navigation}
    actions={[
      { label: 'Open Active Booking', route: ROUTES.CUSTOMER.BOOKING_TRACKING },
    ]}
  />
);

const CustomerProfileScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Customer Profile"
    subtitle="User details, Saved Addresses, Language, Support, Logout"
    role="customer"
    navigation={navigation}
    actions={[
      { label: 'Manage Saved Addresses', route: ROUTES.CUSTOMER.SAVED_ADDRESSES },
      { label: 'Help / Raise a Complaint', route: ROUTES.CUSTOMER.HELP_COMPLAINT },
    ]}
  />
);

const SavedAddressesScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Saved Addresses"
    subtitle="Home, Work, Other address management with GPS auto-fill"
    role="customer"
    navigation={navigation}
  />
);

const HelpComplaintScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Help & Raise Complaint"
    subtitle="Direct complaint filing visible to Cooperative Administrator"
    role="customer"
    navigation={navigation}
  />
);

// --- Home Stack ---
const CustomerHomeStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: '#F8FAFC' },
      headerTitleStyle: { color: '#0F172A', fontWeight: '600' },
    }}
  >
    <Stack.Screen
      name={ROUTES.CUSTOMER.HOME}
      component={CustomerHomeScreen}
      options={{ title: 'SevaSangam Home' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.WORKER_LIST}
      component={WorkerListScreen}
      options={{ title: 'Verified Workers' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.WORKER_PROFILE}
      component={WorkerProfileScreen}
      options={{ title: 'Worker Profile' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.BOOKING_FLOW}
      component={BookingFlowScreen}
      options={{ title: 'Schedule Service' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.EMERGENCY_BOOKING}
      component={EmergencyBookingScreen}
      options={{ title: '⚡ Emergency Request' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.BOOKING_TRACKING}
      component={BookingTrackingScreen}
      options={{ title: 'Track Booking' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.BOOKING_DETAIL}
      component={BookingDetailScreen}
      options={{ title: 'Booking Detail' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.RATE_REVIEW}
      component={RateReviewScreen}
      options={{ title: 'Review & Feedback' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.HELP_COMPLAINT}
      component={HelpComplaintScreen}
      options={{ title: 'Raise Complaint' }}
    />
  </Stack.Navigator>
);

// --- Bookings Stack ---
const CustomerBookingsStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: '#F8FAFC' },
      headerTitleStyle: { color: '#0F172A', fontWeight: '600' },
    }}
  >
    <Stack.Screen
      name={ROUTES.CUSTOMER.BOOKING_HISTORY}
      component={CustomerBookingsScreen}
      options={{ title: 'My Bookings' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.BOOKING_DETAIL}
      component={BookingDetailScreen}
      options={{ title: 'Booking Detail' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.BOOKING_TRACKING}
      component={BookingTrackingScreen}
      options={{ title: 'Track Booking' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.RATE_REVIEW}
      component={RateReviewScreen}
      options={{ title: 'Review Service' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.HELP_COMPLAINT}
      component={HelpComplaintScreen}
      options={{ title: 'Support & Complaints' }}
    />
  </Stack.Navigator>
);

// --- Profile Stack ---
const CustomerProfileStack = () => (
  <Stack.Navigator
    screenOptions={{
      headerStyle: { backgroundColor: '#F8FAFC' },
      headerTitleStyle: { color: '#0F172A', fontWeight: '600' },
    }}
  >
    <Stack.Screen
      name={ROUTES.CUSTOMER.PROFILE}
      component={CustomerProfileScreen}
      options={{ title: 'Profile' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.SAVED_ADDRESSES}
      component={SavedAddressesScreen}
      options={{ title: 'Saved Addresses' }}
    />
    <Stack.Screen
      name={ROUTES.CUSTOMER.HELP_COMPLAINT}
      component={HelpComplaintScreen}
      options={{ title: 'Help & Complaints' }}
    />
  </Stack.Navigator>
);

export const CustomerNavigator = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: '#2563EB',
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
          if (route.name === ROUTES.CUSTOMER.BOOKINGS_TAB) label = 'Bookings';
          if (route.name === ROUTES.CUSTOMER.NOTIFICATIONS_TAB) label = 'Alerts';
          if (route.name === ROUTES.CUSTOMER.PROFILE_TAB) label = 'Profile';
          return (
            <Text style={{ fontSize: 11, fontWeight: focused ? '700' : '500', color }}>
              {label}
            </Text>
          );
        },
        tabBarIcon: ({ focused, color }) => {
          let icon = '🏠';
          if (route.name === ROUTES.CUSTOMER.BOOKINGS_TAB) icon = '📋';
          if (route.name === ROUTES.CUSTOMER.NOTIFICATIONS_TAB) icon = '🔔';
          if (route.name === ROUTES.CUSTOMER.PROFILE_TAB) icon = '👤';
          return <Text style={{ fontSize: 18 }}>{icon}</Text>;
        },
      })}
    >
      <Tab.Screen name={ROUTES.CUSTOMER.HOME_TAB} component={CustomerHomeStack} />
      <Tab.Screen name={ROUTES.CUSTOMER.BOOKINGS_TAB} component={CustomerBookingsStack} />
      <Tab.Screen
        name={ROUTES.CUSTOMER.NOTIFICATIONS_TAB}
        component={CustomerNotificationsScreen}
        options={{ headerShown: true, title: 'Notifications' }}
      />
      <Tab.Screen name={ROUTES.CUSTOMER.PROFILE_TAB} component={CustomerProfileStack} />
    </Tab.Navigator>
  );
};

export default CustomerNavigator;
