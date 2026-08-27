import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { colors, spacing, typography } from '@/theme/tokens';
import { useAuth } from '@/state/auth';
import { notificationsApi } from '@/api/endpoints';

import LoginScreen from '@/screens/auth/LoginScreen';
import RegisterScreen from '@/screens/auth/RegisterScreen';
import OnboardingScreen from '@/screens/onboarding/OnboardingScreen';
import HomeScreen from '@/screens/home/HomeScreen';
import StylistScreen from '@/screens/stylist/StylistScreen';
import DesignerChatScreen from '@/screens/designer/DesignerChatScreen';
import WardrobeScreen from '@/screens/wardrobe/WardrobeScreen';
import ProfileScreen from '@/screens/profile/ProfileScreen';
import SavedLooksScreen from '@/screens/looks/SavedLooksScreen';
import SocialFeedScreen from '@/screens/social/SocialFeedScreen';
import PostDetailScreen from '@/screens/social/PostDetailScreen';
import CreatePostScreen from '@/screens/social/CreatePostScreen';
import PublicProfileScreen from '@/screens/social/PublicProfileScreen';
import NotificationsScreen from '@/screens/notifications/NotificationsScreen';
import XPDashboardScreen from '@/screens/xp/XPDashboardScreen';
import LeaderboardScreen from '@/screens/xp/LeaderboardScreen';
import ChallengesScreen from '@/screens/xp/ChallengesScreen';
import ChallengeDetailScreen from '@/screens/xp/ChallengeDetailScreen';
import RewardsScreen from '@/screens/xp/RewardsScreen';
import MarketplaceScreen from '@/screens/marketplace/MarketplaceScreen';
import ProductDetailScreen from '@/screens/marketplace/ProductDetailScreen';
import OrdersScreen from '@/screens/orders/OrdersScreen';
import OrderDetailScreen from '@/screens/orders/OrderDetailScreen';
import ChatListScreen from '@/screens/chat/ChatListScreen';
import ChatThreadScreen from '@/screens/chat/ChatThreadScreen';
import DesignersScreen from '@/screens/designers/DesignersScreen';
import DesignerDetailScreen from '@/screens/designers/DesignerDetailScreen';
import BecomeDesignerScreen from '@/screens/designers/BecomeDesignerScreen';
import BrandsScreen from '@/screens/brands/BrandsScreen';
import BecomeBrandScreen from '@/screens/brands/BecomeBrandScreen';
import BrandDetailScreen from '@/screens/brands/BrandDetailScreen';
import MyProductsScreen from '@/screens/marketplace/MyProductsScreen';
import CreateProductScreen from '@/screens/marketplace/CreateProductScreen';
import CreatorsScreen from '@/screens/creators/CreatorsScreen';
import BecomeCreatorScreen from '@/screens/creators/BecomeCreatorScreen';
import CampaignsScreen from '@/screens/creators/CampaignsScreen';
import CreateCampaignScreen from '@/screens/creators/CreateCampaignScreen';
import CampaignDetailScreen from '@/screens/creators/CampaignDetailScreen';
import TrendsScreen from '@/screens/trends/TrendsScreen';
import TryOnScreen from '@/screens/trends/TryOnScreen';
import LanguageScreen from '@/screens/language/LanguageScreen';
import QuotesScreen from '@/screens/quotes/QuotesScreen';
import QuoteRequestScreen from '@/screens/quotes/QuoteRequestScreen';
import QuoteDetailScreen from '@/screens/quotes/QuoteDetailScreen';
import PaymentScreen from '@/screens/payments/PaymentScreen';
import ReportScreen from '@/screens/social/ReportScreen';
import type { RootStackParamList } from './types';

export type { RootStackParamList };

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tabs = createBottomTabNavigator();

function TabIcon({ glyph, focused }: { glyph: string; focused: boolean }) {
  return (
    <Text style={{ color: focused ? colors.gold : colors.textMuted, fontSize: 20 }}>{glyph}</Text>
  );
}

function NotificationBadge({ count }: { count: number }) {
  if (count <= 0) return null;
  return (
    <View
      style={{
        backgroundColor: colors.danger,
        borderRadius: 10,
        minWidth: 18,
        height: 18,
        alignItems: 'center',
        justifyContent: 'center',
        position: 'absolute',
        top: -4,
        right: -10,
        paddingHorizontal: 4,
      }}
    >
      <Text style={{ color: colors.white, fontSize: 10, fontWeight: '700' }}>
        {count > 99 ? '99+' : count}
      </Text>
    </View>
  );
}

function MainTabs() {
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await notificationsApi.list();
        setUnread(data.unread);
      } catch { /* ignore */ }
    };
    load();
    const interval = setInterval(load, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Tabs.Navigator
      screenOptions={{
        headerShown: false,
        tabBarActiveTintColor: colors.gold,
        tabBarInactiveTintColor: colors.textMuted,
        tabBarStyle: {
          backgroundColor: colors.inkElevated,
          borderTopColor: colors.inkBorder,
          height: 76,
          paddingBottom: spacing.sm,
          paddingTop: 6,
        },
        tabBarItemStyle: { borderRadius: 14, marginHorizontal: 2 },
        tabBarLabelStyle: { ...typography.micro, fontSize: 10 },
      }}
    >
      <Tabs.Screen
        name="Home"
        component={HomeScreen}
        options={{ tabBarIcon: ({ focused }) => <TabIcon glyph="✦" focused={focused} /> }}
      />
      <Tabs.Screen
        name="Social"
        component={SocialFeedScreen}
        options={{
          tabBarIcon: ({ focused }) => (
            <View>
              <TabIcon glyph="♡" focused={focused} />
              <NotificationBadge count={unread} />
            </View>
          ),
        }}
      />
      <Tabs.Screen
        name="Stylist"
        component={StylistScreen}
        options={{ tabBarIcon: ({ focused }) => <TabIcon glyph="✂" focused={focused} /> }}
      />
      <Tabs.Screen
        name="Shop"
        component={MarketplaceScreen}
        options={{ tabBarIcon: ({ focused }) => <TabIcon glyph="◈" focused={focused} /> }}
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
          <Stack.Screen name="Trends" component={TrendsScreen} />
          <Stack.Screen name="TryOn" component={TryOnScreen} />
          <Stack.Screen name="Language" component={LanguageScreen} />
          <Stack.Screen name="PostDetail" component={PostDetailScreen} />
          <Stack.Screen name="CreatePost" component={CreatePostScreen} />
          <Stack.Screen name="PublicProfile" component={PublicProfileScreen} />
          <Stack.Screen name="Notifications" component={NotificationsScreen} />
          <Stack.Screen name="XPDashboard" component={XPDashboardScreen} />
          <Stack.Screen name="Leaderboard" component={LeaderboardScreen} />
          <Stack.Screen name="Challenges" component={ChallengesScreen} />
          <Stack.Screen name="ChallengeDetail" component={ChallengeDetailScreen} />
          <Stack.Screen name="Rewards" component={RewardsScreen} />
          <Stack.Screen name="ProductDetail" component={ProductDetailScreen} />
          <Stack.Screen name="Orders" component={OrdersScreen} />
          <Stack.Screen name="OrderDetail" component={OrderDetailScreen} />
          <Stack.Screen name="ChatList" component={ChatListScreen} />
          <Stack.Screen name="ChatThread" component={ChatThreadScreen} />
          <Stack.Screen name="Designers" component={DesignersScreen} />
          <Stack.Screen name="DesignerDetail" component={DesignerDetailScreen} />
          <Stack.Screen name="BecomeDesigner" component={BecomeDesignerScreen} />
          <Stack.Screen name="Brands" component={BrandsScreen} />
          <Stack.Screen name="BecomeBrand" component={BecomeBrandScreen} />
          <Stack.Screen name="BrandDetail" component={BrandDetailScreen} />
          <Stack.Screen name="MyProducts" component={MyProductsScreen} />
          <Stack.Screen name="CreateProduct" component={CreateProductScreen} />
          <Stack.Screen name="Creators" component={CreatorsScreen} />
          <Stack.Screen name="BecomeCreator" component={BecomeCreatorScreen} />
          <Stack.Screen name="Campaigns" component={CampaignsScreen} />
          <Stack.Screen name="CreateCampaign" component={CreateCampaignScreen} />
          <Stack.Screen name="CampaignDetail" component={CampaignDetailScreen} />
          <Stack.Screen name="Quotes" component={QuotesScreen} />
          <Stack.Screen name="QuoteRequestScreen" component={QuoteRequestScreen} />
          <Stack.Screen name="QuoteDetail" component={QuoteDetailScreen} />
          <Stack.Screen name="Payment" component={PaymentScreen} />
          <Stack.Screen name="Report" component={ReportScreen} />
        </Stack.Navigator>
      )}
    </NavigationContainer>
  );
}
