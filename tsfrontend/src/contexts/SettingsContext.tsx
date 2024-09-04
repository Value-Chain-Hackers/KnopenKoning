import React, { createContext, useState, useContext, useEffect, ReactNode } from 'react';

// Define the shape of your settings
interface Settings {
  apiUrl: string;
  theme: string;
  maxItemsPerPage: number;
  featureFlags: {
    newUserInterface: boolean;
    betaFeatures: boolean;
  };
}

const SettingsContext = createContext<Settings | null>(null);

export const SettingsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<Settings | null>(null);

  useEffect(() => {
    fetch('/settings.json')
      .then(response => response.json())
      .then(data => setSettings(data))
      .catch(error => console.error('Error loading settings:', error));
  }, []);

  return (
    <SettingsContext.Provider value={settings}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (context === null) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};