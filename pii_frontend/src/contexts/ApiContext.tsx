"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ApiConfig, initializeApiClient, getApiClient } from '@/lib/api';

interface ApiContextType {
  config: ApiConfig;
  updateConfig: (newConfig: Partial<ApiConfig>) => void;
  isConnected: boolean;
  testConnection: () => Promise<{ success: boolean; error?: string; details?: any }>;
}

const ApiContext = createContext<ApiContextType | undefined>(undefined);

export const useApi = () => {
  const context = useContext(ApiContext);
  if (!context) {
    throw new Error('useApi must be used within an ApiProvider');
  }
  return context;
};

interface ApiProviderProps {
  children: ReactNode;
}

export const ApiProvider: React.FC<ApiProviderProps> = ({ children }) => {
  const [config, setConfig] = useState<ApiConfig>({
    baseUrl: 'http://localhost:18000',
    token: 'your-secret-token',
    timeout: 30
  });
  const [isConnected, setIsConnected] = useState(false);

  // 설정 로드
  useEffect(() => {
    const savedConfig = localStorage.getItem('api-config');
    if (savedConfig) {
      try {
        const parsed = JSON.parse(savedConfig);
        setConfig(prev => ({ ...prev, ...parsed }));
      } catch (error) {
        console.error('설정 로드 실패:', error);
      }
    }
  }, []);

  // API 클라이언트 초기화
  useEffect(() => {
    initializeApiClient(config);
  }, [config]);

  const updateConfig = (newConfig: Partial<ApiConfig>) => {
    const updatedConfig = { ...config, ...newConfig };
    setConfig(updatedConfig);
    localStorage.setItem('api-config', JSON.stringify(updatedConfig));
    initializeApiClient(updatedConfig);
  };

  const testConnection = async (): Promise<{ success: boolean; error?: string; details?: any }> => {
    try {
      console.log('🔍 연결 테스트 시작:', config.baseUrl);
      const client = getApiClient();
      const result = await client.testBackendConnection();
      
      console.log('📡 API 응답:', result);
      
      if (result.success) {
        setIsConnected(true);
        return { success: true, details: result };
      } else {
        setIsConnected(false);
        return { 
          success: false, 
          error: `API 호출 실패: ${result.error || '알 수 없는 오류'}`,
          details: result 
        };
      }
    } catch (error) {
      console.error('❌ 연결 테스트 중 오류:', error);
      setIsConnected(false);
      
      let errorMessage = '알 수 없는 오류';
      let details = error;
      
      if (error instanceof TypeError && error.message.includes('fetch')) {
        errorMessage = `네트워크 오류: ${config.baseUrl}에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.`;
      } else if (error instanceof Error) {
        errorMessage = error.message;
      }
      
      return { 
        success: false, 
        error: errorMessage,
        details 
      };
    }
  };

  return (
    <ApiContext.Provider value={{
      config,
      updateConfig,
      isConnected,
      testConnection
    }}>
      {children}
    </ApiContext.Provider>
  );
}; 