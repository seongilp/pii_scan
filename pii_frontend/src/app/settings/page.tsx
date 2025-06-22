"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Textarea } from "@/components/ui/textarea";
import { 
  User, 
  Shield, 
  Bell, 
  Database, 
  Palette, 
  Download,
  Upload,
  Save,
  RefreshCw,
  Trash2,
  Eye,
  EyeOff,
  Server,
  Key,
  TestTube,
  CheckCircle,
  XCircle
} from "lucide-react";
import { useState, useEffect } from "react";
import { testBackendConnection } from "@/lib/api";
import { useApi } from "@/contexts/ApiContext";

export default function SettingsPage() {
  const { config, updateConfig, isConnected, testConnection } = useApi();
  const [showPassword, setShowPassword] = useState(false);
  const [showToken, setShowToken] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; error?: string; details?: any } | null>(null);
  const [isTesting, setIsTesting] = useState(false);
  
  // 설정 상태
  const [settings, setSettings] = useState({
    backendUrl: 'http://localhost:18000',
    apiVersion: 'v1',
    apiToken: 'your-secret-token',
    connectionTimeout: 30,
    autoReconnect: true,
    scanEndpoint: '/scan',
    jobsEndpoint: '/jobs',
    resultsEndpoint: '/results',
    configEndpoint: '/database-configs',
    healthEndpoint: '/health'
  });

  // 설정 로드 (로컬 스토리지에서)
  useEffect(() => {
    const savedSettings = localStorage.getItem('app-settings');
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings(prev => ({ ...prev, ...parsed }));
      } catch (error) {
        console.error('설정 로드 실패:', error);
      }
    }
  }, []);

  // 설정 저장
  const saveSettings = () => {
    localStorage.setItem('app-settings', JSON.stringify(settings));
    // 여기서 실제 API 호출로 설정을 서버에 저장할 수도 있습니다
  };

  const handleSave = () => {
    // TODO: Implement save logic
    console.log('Saved settings:', settings);
    // 상태를 업데이트하고 localStorage에 저장
    updateConfig({
      baseUrl: settings.backendUrl,
      token: settings.apiToken,
      timeout: settings.connectionTimeout
    });
    // 여기서 testConnection을 다시 호출하여 isConnected 상태를 업데이트 할 수 있습니다.
  };

  const handleTestConnection = async () => {
    setIsTesting(true);
    setTestResult(null);
    
    try {
      const result = await testConnection();
      setTestResult(result);
      
      if (result.success) {
        console.log("✅ 연결 성공");
      } else {
        console.error("❌ 연결 실패", result.error || "알 수 없는 오류가 발생했습니다.");
      }
    } catch (error) {
      setTestResult({ 
        success: false, 
        error: error instanceof Error ? error.message : '알 수 없는 오류' 
      });
    } finally {
      setIsTesting(false);
    }
  };

  // 현재 API 컨텍스트의 설정을 로컬 상태로 동기화
  useEffect(() => {
    setSettings({
      backendUrl: config.baseUrl || 'http://localhost:18000',
      apiVersion: 'v1', // 이 값은 config에 추가해야 할 수 있습니다.
      apiToken: config.token || 'your-secret-token',
      connectionTimeout: config.timeout || 30,
      autoReconnect: true,
      scanEndpoint: '/scan',
      jobsEndpoint: '/jobs',
      resultsEndpoint: '/results',
      configEndpoint: '/database-configs',
      healthEndpoint: '/health'
    });
  }, [config]);

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">설정</h2>
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={() => {
            setSettings({
              backendUrl: 'http://localhost:18000',
              apiVersion: 'v1',
              apiToken: 'your-secret-token',
              connectionTimeout: 30,
              autoReconnect: true,
              scanEndpoint: '/scan',
              jobsEndpoint: '/jobs',
              resultsEndpoint: '/results',
              configEndpoint: '/database-configs',
              healthEndpoint: '/health'
            });
          }}>
            <RefreshCw className="mr-2 h-4 w-4" />
            기본값으로 복원
          </Button>
          <Button onClick={saveSettings}>
            <Save className="mr-2 h-4 w-4" />
            설정 저장
          </Button>
        </div>
      </div>
      
      <div className="grid gap-6">
        {/* 백엔드 연결 설정 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Server className="h-5 w-5" />
              백엔드 연결 설정
            </CardTitle>
            <CardDescription>
              PII Scanner 백엔드 API 서버 연결 정보를 설정하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="backend-url">백엔드 서버 URL</Label>
                <Input 
                  id="backend-url" 
                  placeholder="http://localhost:18000"
                  value={settings.backendUrl}
                  onChange={(e) => setSettings(prev => ({ ...prev, backendUrl: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="api-version">API 버전</Label>
                <Input 
                  id="api-version" 
                  placeholder="v1"
                  value={settings.apiVersion}
                  onChange={(e) => setSettings(prev => ({ ...prev, apiVersion: e.target.value }))}
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="api-token">API 인증 토큰</Label>
              <div className="relative">
                <Input 
                  id="api-token" 
                  type={showToken ? "text" : "password"}
                  placeholder="your-secret-token"
                  value={settings.apiToken}
                  onChange={(e) => setSettings(prev => ({ ...prev, apiToken: e.target.value }))}
                />
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowToken(!showToken)}
                >
                  {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                백엔드에서 설정한 인증 토큰을 입력하세요
              </p>
            </div>

            <div className="flex items-center space-x-4">
              <Button 
                variant="outline" 
                onClick={handleTestConnection}
                disabled={isTesting}
              >
                {isTesting ? (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    연결 테스트 중...
                  </>
                ) : (
                  <>
                    <TestTube className="mr-2 h-4 w-4" />
                    연결 테스트
                  </>
                )}
              </Button>
              
              {testResult && (
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle className="h-4 w-4" />
                  <span className="text-sm">{testResult.success ? "연결 성공" : testResult.error}</span>
                </div>
              )}
            </div>

            <Separator />

            <div className="space-y-2">
              <Label>연결 설정</Label>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label className="text-sm">자동 재연결</Label>
                    <p className="text-xs text-muted-foreground">
                      연결이 끊어졌을 때 자동으로 재연결을 시도합니다
                    </p>
                  </div>
                  <Switch 
                    checked={settings.autoReconnect}
                    onCheckedChange={(checked) => setSettings(prev => ({ ...prev, autoReconnect: checked }))}
                  />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label className="text-sm">연결 타임아웃</Label>
                    <p className="text-xs text-muted-foreground">
                      API 요청 타임아웃 시간을 설정합니다
                    </p>
                  </div>
                  <Select 
                    value={settings.connectionTimeout.toString()}
                    onValueChange={(value) => setSettings(prev => ({ ...prev, connectionTimeout: parseInt(value) }))}
                  >
                    <SelectTrigger className="w-24">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="10">10초</SelectItem>
                      <SelectItem value="30">30초</SelectItem>
                      <SelectItem value="60">60초</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* API 엔드포인트 설정 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              API 엔드포인트 설정
            </CardTitle>
            <CardDescription>
              백엔드 API 엔드포인트 경로를 설정하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="scan-endpoint">스캔 엔드포인트</Label>
                <Input 
                  id="scan-endpoint" 
                  value={settings.scanEndpoint}
                  onChange={(e) => setSettings(prev => ({ ...prev, scanEndpoint: e.target.value }))}
                  placeholder="/scan"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="jobs-endpoint">작업 관리 엔드포인트</Label>
                <Input 
                  id="jobs-endpoint" 
                  value={settings.jobsEndpoint}
                  onChange={(e) => setSettings(prev => ({ ...prev, jobsEndpoint: e.target.value }))}
                  placeholder="/jobs"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="results-endpoint">결과 조회 엔드포인트</Label>
                <Input 
                  id="results-endpoint" 
                  value={settings.resultsEndpoint}
                  onChange={(e) => setSettings(prev => ({ ...prev, resultsEndpoint: e.target.value }))}
                  placeholder="/results"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="config-endpoint">설정 관리 엔드포인트</Label>
                <Input 
                  id="config-endpoint" 
                  value={settings.configEndpoint}
                  onChange={(e) => setSettings(prev => ({ ...prev, configEndpoint: e.target.value }))}
                  placeholder="/database-configs"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="health-endpoint">헬스체크 엔드포인트</Label>
              <Input 
                id="health-endpoint" 
                value={settings.healthEndpoint}
                onChange={(e) => setSettings(prev => ({ ...prev, healthEndpoint: e.target.value }))}
                placeholder="/health"
              />
            </div>
          </CardContent>
        </Card>

        {/* 계정 설정 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              계정 설정
            </CardTitle>
            <CardDescription>
              사용자 정보와 인증 설정을 관리하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="username">사용자명</Label>
                <Input id="username" defaultValue="admin" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">이메일</Label>
                <Input id="email" type="email" defaultValue="admin@company.com" />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="current-password">현재 비밀번호</Label>
                <div className="relative">
                  <Input id="current-password" type="password" />
                  <Button variant="ghost" size="icon" className="absolute right-0 top-0 h-full px-3">
                    <Eye className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-password">새 비밀번호</Label>
                <div className="relative">
                  <Input id="new-password" type="password" />
                  <Button variant="ghost" size="icon" className="absolute right-0 top-0 h-full px-3">
                    <Eye className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 보안 설정 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              보안 설정
            </CardTitle>
            <CardDescription>
              보안 및 개인정보 보호 관련 설정
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>2단계 인증</Label>
                <p className="text-sm text-muted-foreground">
                  로그인 시 추가 보안을 위해 2단계 인증을 활성화합니다
                </p>
              </div>
              <Switch />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>세션 자동 로그아웃</Label>
                <p className="text-sm text-muted-foreground">
                  일정 시간 후 자동으로 로그아웃됩니다
                </p>
              </div>
              <Select defaultValue="30">
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="15">15분</SelectItem>
                  <SelectItem value="30">30분</SelectItem>
                  <SelectItem value="60">1시간</SelectItem>
                  <SelectItem value="120">2시간</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>로그인 알림</Label>
                <p className="text-sm text-muted-foreground">
                  새로운 기기에서 로그인 시 이메일 알림을 받습니다
                </p>
              </div>
              <Switch defaultChecked />
            </div>
          </CardContent>
        </Card>

        {/* 알림 설정 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              알림 설정
            </CardTitle>
            <CardDescription>
              스캔 작업 및 보안 알림 설정을 관리하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>스캔 완료 알림</Label>
                <p className="text-sm text-muted-foreground">
                  스캔 작업이 완료되면 알림을 받습니다
                </p>
              </div>
              <Switch defaultChecked />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>고위험 패턴 발견 알림</Label>
                <p className="text-sm text-muted-foreground">
                  고위험 개인정보 패턴 발견 시 즉시 알림을 받습니다
                </p>
              </div>
              <Switch defaultChecked />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>이메일 알림</Label>
                <p className="text-sm text-muted-foreground">
                  중요한 알림을 이메일로도 받습니다
                </p>
              </div>
              <Switch />
            </div>
          </CardContent>
        </Card>

        {/* 스캔 설정 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              스캔 설정
            </CardTitle>
            <CardDescription>
              데이터베이스 스캔 관련 기본 설정을 관리하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="default-sample-size">기본 샘플 크기</Label>
                <Input id="default-sample-size" type="number" defaultValue="100" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="max-concurrent-scans">최대 동시 스캔 수</Label>
                <Input id="max-concurrent-scans" type="number" defaultValue="3" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>자동 스캔 스케줄링</Label>
                <p className="text-sm text-muted-foreground">
                  정기적으로 데이터베이스를 자동 스캔합니다
                </p>
              </div>
              <Switch />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>스캔 결과 자동 저장</Label>
                <p className="text-sm text-muted-foreground">
                  스캔 완료 시 결과를 자동으로 저장합니다
                </p>
              </div>
              <Switch defaultChecked />
            </div>
          </CardContent>
        </Card>

        {/* 테마 설정 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Palette className="h-5 w-5" />
              테마 설정
            </CardTitle>
            <CardDescription>
              인터페이스 테마와 색상을 설정하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>테마 모드</Label>
              <Select defaultValue="light">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">라이트 모드</SelectItem>
                  <SelectItem value="dark">다크 모드</SelectItem>
                  <SelectItem value="auto">시스템 설정 따르기</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>주 색상</Label>
              <Select defaultValue="blue">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="blue">파란색</SelectItem>
                  <SelectItem value="green">초록색</SelectItem>
                  <SelectItem value="purple">보라색</SelectItem>
                  <SelectItem value="orange">주황색</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* 데이터 관리 */}
        <Card>
          <CardHeader>
            <CardTitle>데이터 관리</CardTitle>
            <CardDescription>
              스캔 결과 및 설정 데이터를 관리하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-4">
              <Button variant="outline">
                <Download className="mr-2 h-4 w-4" />
                설정 내보내기
              </Button>
              <Button variant="outline">
                <Upload className="mr-2 h-4 w-4" />
                설정 가져오기
              </Button>
            </div>
            <Separator />
            <div className="space-y-2">
              <Label>데이터 정리</Label>
              <div className="flex items-center space-x-4">
                <Button variant="outline" size="sm">
                  <Trash2 className="mr-2 h-4 w-4" />
                  30일 이상 된 스캔 결과 삭제
                </Button>
                <Button variant="outline" size="sm">
                  <Trash2 className="mr-2 h-4 w-4" />
                  모든 캐시 데이터 삭제
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 백엔드 연결 테스트 결과 표시 */}
        {testResult && (
          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {testResult.success ? (
                  <>
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    연결 테스트 결과
                  </>
                ) : (
                  <>
                    <XCircle className="h-5 w-5 text-red-500" />
                    연결 테스트 실패
                  </>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {testResult.success ? (
                <div className="text-green-600">
                  <p>✅ 백엔드 서버에 성공적으로 연결되었습니다.</p>
                  {testResult.details && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-sm text-gray-600">응답 상세 정보</summary>
                      <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto">
                        {JSON.stringify(testResult.details, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              ) : (
                <div className="text-red-600">
                  <p className="font-medium">❌ {testResult.error}</p>
                  {testResult.details && (
                    <details className="mt-2">
                      <summary className="cursor-pointer text-sm text-gray-600">오류 상세 정보</summary>
                      <pre className="mt-2 text-xs bg-red-50 p-2 rounded overflow-auto">
                        {JSON.stringify(testResult.details, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
} 