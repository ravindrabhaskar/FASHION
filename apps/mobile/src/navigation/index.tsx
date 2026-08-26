import React from 'react';
import { Text } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { colors, spacing, typography } from '@/theme/tokens';
import { useAuth } from '@/state/auth';

import LoginScreen from '@/screens/auth/LoginScreen';
import RegisterScreen from '@/screens/auth/RegisterScreen';
import OnboardingScreen from '@/screens/onboarding/OnboardingScreen';
import HomeScreen from '@/screens/home/HomeScreen';
import StylistScreen from '@/screens/stylist/StylistScreen';
import DesignerChatScreen from '@/screens/designer/DesignerChatScreen';
import WardrobeScreen from '@/screens/wardrobe/WardrobeScreen';
import ProfileScreen from '@/screens/profile/ProfileScreen';
import SavedLooksScreen from '@/screens/looks/SavedLooksScreen';
import type { RootStackParamList } from './types';

export type { RootStackParamList };

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tabs = createBottomTabNavigator();

function TabIcon({ glyph, focused }: { glyph: string; focused: boolean }) {
  return (
    <Text style={{ color: focused ? colors.gold : colors.textMuted, fontSize: 20 }}>{glyph}</Text>
  );
}

function MainTabs() {
  return (
    <Tabs.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.gold,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.inkElevated,
          borderTopColor: colors.inkBorder,
          height: 84,
          paddingBottom: spacing.md,
          paddingTop: spacing.sm,
        },
        tabBarLabelStyle: { ...typography.micro },
      }}
    >
      <Tabs.Screen
        name="Home"
        component={HomeScreen}
        options={{ tabBarIcon: ({ focused }) => <TabIcon glyph="✦" focused={focused} /> }}
      />
      <Tabs.Screen
        name="Stylist"
        component={StylistScreen}
        options={{ tabBarIcon: ({ focused }) => <TabIcon glyph="✂" focused={focused} /> }}
      />
      <Tabs.Screen
        name="Wardrobe"
        component={WardrobeScreen}
        options={{ tabBarIcon: ({ focused }) => <TabIcon glyph="▤" focused={focused} /> }}
      />
      <Tabs.Screen
        name="Profile"
        component={ProfileScreen}
        options={{ tabBarIcon: ({ focused }) => <TabIcon glyph="◉" focused={focused} /> }}
      />
    </Tabs.Navigator>
  );
}

const AuthStack = () => (
  <Stack.Navigator screenOptions={{ headerShown: false }}>
    <Stack.Screen name="Login" component={LoginScreen} />
    <Stack.Screen name="Register" component={RegisterScreen} />
  </Stack.Navigator>
);

export function RootNavigator() {
  const { user } = useAuth();
  return (
    <NavigationContainer>
      {!user ? (
        <AuthStack />
      ) : !user.onboarding_completed_at ? (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Onboarding" component={OnboardingScreen} />
        </Stack.Navigator>
      ) : (
        <Stack.Navigator screenOptions={{ headerShown: false }}>
          <Stack.Screen name="Main" component={MainTabs} />
          <Stack.Screen name="SavedLooks" component={SavedLooksScreen} />
          <Stack.Screen
            name="DesignerChat"
            component={DesignerChatScreen}
            options={{ animation: 'slide_from_bottom' }}
          />
        </Stack.Navigator>
      )}
    </NavigationContainer>
  );
}
