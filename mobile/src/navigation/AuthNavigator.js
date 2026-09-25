import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import ROUTES from './routes';

// Real auth screen imports
import Splash from '../screens/auth/Splash';
import LanguageSelect from '../screens/auth/LanguageSelect';
import Onboarding from '../screens/auth/Onboarding';
import Login from '../screens/auth/Login';
import VerifyOtp from '../screens/auth/VerifyOtp';
import RoleSelect from '../screens/auth/RoleSelect';

const Stack = createNativeStackNavigator();

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
        component={Splash}
        options={{ headerShown: false }}
      />
      <Stack.Screen
        name={ROUTES.AUTH.LANGUAGE_SELECT}
        component={LanguageSelect}
        options={{ title: 'Select Language', headerShown: false }}
      />
      <Stack.Screen
        name={ROUTES.AUTH.ONBOARDING}
        component={Onboarding}
        options={{ title: 'Welcome to SevaSangam', headerShown: false }}
      />
      <Stack.Screen
        name={ROUTES.AUTH.LOGIN}
        component={Login}
        options={{ title: 'Login', headerShown: false }}
      />
      <Stack.Screen
        name={ROUTES.AUTH.VERIFY_OTP}
        component={VerifyOtp}
        options={{ title: 'Verify OTP', headerShown: false }}
      />
      <Stack.Screen
        name={ROUTES.AUTH.ROLE_SELECT}
        component={RoleSelect}
        options={{ title: 'Select Profile', headerShown: false }}
      />
    </Stack.Navigator>
  );
};

export default AuthNavigator;

