import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import ROUTES from './routes';
import ScreenPlaceholder from '../screens/placeholder/ScreenPlaceholder';

const Stack = createNativeStackNavigator();

// Placeholder screens with realistic next-step actions for testing navigation
const SplashScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Splash Screen"
    subtitle="App initialization & session restoration"
    role="auth"
    navigation={navigation}
    actions={[
      { label: 'Proceed to Language Select', route: ROUTES.AUTH.LANGUAGE_SELECT },
      { label: 'Skip to Login', route: ROUTES.AUTH.LOGIN },
    ]}
  />
);

const LanguageSelectScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Language Selection"
    subtitle="Select English, Hindi (हिन्दी) or Marathi (मराठी)"
    role="auth"
    navigation={navigation}
    actions={[
      { label: 'Continue to Onboarding', route: ROUTES.AUTH.ONBOARDING },
      { label: 'Skip directly to Login', route: ROUTES.AUTH.LOGIN },
    ]}
  />
);

const OnboardingScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Onboarding Carousel"
    subtitle="3 swipeable slides highlighting cooperative trust & features"
    role="auth"
    navigation={navigation}
    actions={[
      { label: 'Get Started (Go to Login)', route: ROUTES.AUTH.LOGIN },
      { label: 'Back to Language Select', route: ROUTES.AUTH.LANGUAGE_SELECT },
    ]}
  />
);

const LoginScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Phone Login"
    subtitle="Enter 10-digit phone number (+91)"
    role="auth"
    navigation={navigation}
    actions={[
      { label: 'Send OTP (Go to Verify OTP)', route: ROUTES.AUTH.VERIFY_OTP },
      { label: 'Back to Onboarding', route: ROUTES.AUTH.ONBOARDING },
    ]}
  />
);

const VerifyOtpScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Verify OTP"
    subtitle="Enter 6-digit OTP code (mock: 123456)"
    role="auth"
    navigation={navigation}
    actions={[
      { label: 'Verify Success (New user -> Role Select)', route: ROUTES.AUTH.ROLE_SELECT },
      { label: 'Change Phone Number', route: ROUTES.AUTH.LOGIN },
    ]}
  />
);

const RoleSelectScreen = ({ navigation }) => (
  <ScreenPlaceholder
    title="Choose Profile / Role"
    subtitle="Choose between Customer and Worker (Admin is pre-provisioned)"
    role="auth"
    navigation={navigation}
    actions={[
      { label: 'Back to Login', route: ROUTES.AUTH.LOGIN },
    ]}
  />
);

export const AuthNavigator = () => {
  return (
    <Stack.Navigator
      initialRouteName={ROUTES.AUTH.SPLASH}
      screenOptions={{
        headerShown: true,
        headerStyle: { backgroundColor: '#F8FAFC' },
        headerTitleStyle: { color: '#0F172A', fontWeight: '600' },
      }}
    >
      <Stack.Screen
        name={ROUTES.AUTH.SPLASH}
        component={SplashScreen}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name={ROUTES.AUTH.LANGUAGE_SELECT}
        component={LanguageSelectScreen}
        options={{ title: 'Select Language' }}
      />
      <Stack.Screen
        name={ROUTES.AUTH.ONBOARDING}
        component={OnboardingScreen}
        options={{ title: 'Welcome to SevaSangam' }}
      />
      <Stack.Screen
        name={ROUTES.AUTH.LOGIN}
        component={LoginScreen}
        options={{ title: 'Login' }}
      />
      <Stack.Screen
        name={ROUTES.AUTH.VERIFY_OTP}
        component={VerifyOtpScreen}
        options={{ title: 'Verify OTP' }}
      />
      <Stack.Screen
        name={ROUTES.AUTH.ROLE_SELECT}
        component={RoleSelectScreen}
        options={{ title: 'Select Profile' }}
      />
    </Stack.Navigator>
  );
};

export default AuthNavigator;
