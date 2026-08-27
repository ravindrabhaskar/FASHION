import AsyncStorage from '@react-native-async-storage/async-storage';
import { Platform } from 'react-native';
import { notificationsApi } from '@/api/endpoints';

const DEVICE_KEY = 'fashionxp.device.id';
const PUSH_KEY = 'fashionxp.push.token';
// Expo Go / dev builds all use the same sandbox experience for push unless a
// development build with expo-notifications config is installed. We try the
// native token first and gracefully fall back to a stable per-install id.
let expoPushModule: any = null;

function tryLoadExpoNotifications(): any {
  if (expoPushModule !== null) return expoPushModule;
  try {
    // eslint-disable-next-line @typescript-eslint/no-var-requires
    expoPushModule = require('expo-notifications');
  } catch {
    expoPushModule = false;
  }
  return expoPushModule;
}

async function nativeTokenOrNull(): Promise<string | null> {
  const mod = tryLoadExpoNotifications();
  if (!mod?.getExpoPushTokenAsync) return null;
  try {
    if (Platform.OS === 'android') {
      await mod.setNotificationChannelAsync('default', {
        name: 'Default',
        importance: 4,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#FF231F7C',
      });
    }
    const { status } = await mod.getPermissionsAsync();
    if (status !== 'granted') {
      const requested = await mod.requestPermissionsAsync();
      if (requested.status !== 'granted') return null;
    }
    const token = await mod.getExpoPushTokenAsync({ projectId: undefined } as any);
    return typeof token === 'string' ? token : token?.data ?? null;
  } catch {
    return null;
  }
}

export async function registerPushDevice(): Promise<void> {
  try {
    let token = await nativeTokenOrNull();
    if (!token) {
      token = await AsyncStorage.getItem(DEVICE_KEY);
      if (!token) {
        token = `dev-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
        await AsyncStorage.setItem(DEVICE_KEY, token);
      }
    } else if (Platform.OS !== 'web') {
      await AsyncStorage.setItem(PUSH_KEY, token);
    }
    await notificationsApi.registerDevice(token, Platform.OS === 'ios' ? 'ios' : 'android');
  } catch {
    // best-effort: offline or unauth'd sessions are ignored
  }
}