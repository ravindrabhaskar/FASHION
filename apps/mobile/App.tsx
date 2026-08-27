import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { AuthProvider, useAuth } from '@/state/auth';
import { I18nProvider } from '@/i18n';
import { RootNavigator } from '@/navigation';

export default function App() {
  return (
    <AuthProvider>
      <I18nProvider>
        <StatusBar style="light" />
        <RootNavigator />
      </I18nProvider>
    </AuthProvider>
  );
}