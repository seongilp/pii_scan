// API 클라이언트 유틸리티

export interface ApiConfig {
  baseUrl: string;
  token: string;
  timeout: number;
}

interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

class ApiClient {
  private config: ApiConfig;

  constructor(config: ApiConfig) {
    this.config = config;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<ApiResponse<T>> {
    const url = `${this.config.baseUrl}${endpoint}`;
    
    const headers = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.config.token}`,
      ...options.headers,
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.config.timeout * 1000);

    try {
      const response = await fetch(url, {
        ...options,
        headers,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return { success: true, data };
    } catch (error) {
      clearTimeout(timeoutId);
      return { 
        success: false, 
        error: error instanceof Error ? error.message : 'Unknown error' 
      };
    }
  }

  // 백엔드 연결 테스트 (설정 페이지용)
  async testBackendConnection(): Promise<ApiResponse> {
    return this.request('/health');
  }

  // 데이터베이스 연결 테스트
  async testDatabaseConnection(config: any): Promise<ApiResponse> {
    return this.request('/test-connection', {
      method: 'POST',
      body: JSON.stringify(config)
    });
  }

  // 스캔 작업 목록
  async getScanJobs(): Promise<ApiResponse> {
    return this.request('/scan/jobs');
  }

  // 스캔 시작
  async startScan(config: any): Promise<ApiResponse> {
    return this.request('/scan/start', {
      method: 'POST',
      body: JSON.stringify(config)
    });
  }

  // 스캔 결과
  async getScanResults(jobId: string): Promise<ApiResponse> {
    return this.request(`/scan/results/${jobId}`);
  }

  // 통계 데이터
  async getAnalytics(timeRange: string = '30'): Promise<ApiResponse> {
    return this.request(`/analytics?timeRange=${timeRange}`);
  }

  // 대시보드 데이터
  async getDashboard(): Promise<ApiResponse> {
    return this.request('/dashboard');
  }

  // 개인정보 패턴 목록
  async getPatterns(): Promise<ApiResponse> {
    return this.request('/patterns');
  }

  // 설정 저장
  async saveSettings(settings: any): Promise<ApiResponse> {
    return this.request('/settings', {
      method: 'POST',
      body: JSON.stringify(settings)
    });
  }
}

// 싱글톤 인스턴스
let apiClient: ApiClient | null = null;

export const initializeApiClient = (config: ApiConfig) => {
  apiClient = new ApiClient(config);
};

export const getApiClient = (): ApiClient => {
  if (!apiClient) {
    throw new Error('API client not initialized. Call initializeApiClient first.');
  }
  return apiClient;
};

// 편의 함수들
export const api = {
  testBackendConnection: () => getApiClient().testBackendConnection(),
  testDatabaseConnection: (config: any) => getApiClient().testDatabaseConnection(config),
  getScanJobs: () => getApiClient().getScanJobs(),
  startScan: (config: any) => getApiClient().startScan(config),
  getScanResults: (jobId: string) => getApiClient().getScanResults(jobId),
  getAnalytics: (timeRange?: string) => getApiClient().getAnalytics(timeRange),
  getPatterns: () => getApiClient().getPatterns(),
  saveSettings: (settings: any) => getApiClient().saveSettings(settings),
  getDashboard: () => getApiClient().getDashboard(),
};

// 개별 export 함수들
export const testBackendConnection = () => getApiClient().testBackendConnection();
export const testDatabaseConnection = (config: any) => getApiClient().testDatabaseConnection(config);
export const getScanJobs = () => getApiClient().getScanJobs();
export const startScan = (config: any) => getApiClient().startScan(config);
export const getScanResults = (jobId: string) => getApiClient().getScanResults(jobId);
export const getAnalytics = (timeRange?: string) => getApiClient().getAnalytics(timeRange);
export const getPatterns = () => getApiClient().getPatterns();
export const saveSettings = (settings: any) => getApiClient().saveSettings(settings);
export const getDashboard = () => getApiClient().getDashboard();

export type { ApiResponse }; 