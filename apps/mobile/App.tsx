import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { AuthProvider, useAuth } from '@/state/auth';
import { RootNavigator } from '@/navigation';

export default function App() {
  return (
    <AuthProvider>
      <StatusBar style="light" />
      <RootNavigator />
    </AuthProvider>
  );
}
