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
import { useState } from "react";

export default function SettingsPage() {
  const [showToken, setShowToken] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');

  const testConnection = async () => {
    setConnectionStatus('testing');
    // 실제로는 여기서 백엔드 연결을 테스트합니다
    setTimeout(() => {
      setConnectionStatus('success');
      setTimeout(() => setConnectionStatus('idle'), 2000);
    }, 1000);
  };

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">설정</h2>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            기본값으로 복원
          </Button>
          <Button>
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
                  placeholder="http://localhost:8000"
                  defaultValue="http://localhost:8000"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="api-version">API 버전</Label>
                <Input 
                  id="api-version" 
                  placeholder="v1"
                  defaultValue="v1"
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
                  defaultValue="your-secret-token"
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
                onClick={testConnection}
                disabled={connectionStatus === 'testing'}
              >
                {connectionStatus === 'testing' ? (
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
              
              {connectionStatus === 'success' && (
                <div className="flex items-center space-x-2 text-green-600">
                  <CheckCircle className="h-4 w-4" />
                  <span className="text-sm">연결 성공!</span>
                </div>
              )}
              
              {connectionStatus === 'error' && (
                <div className="flex items-center space-x-2 text-red-600">
                  <XCircle className="h-4 w-4" />
                  <span className="text-sm">연결 실패</span>
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
                  <Switch defaultChecked />
                </div>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label className="text-sm">연결 타임아웃</Label>
                    <p className="text-xs text-muted-foreground">
                      API 요청 타임아웃 시간을 설정합니다
                    </p>
                  </div>
                  <Select defaultValue="30">
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
                  defaultValue="/scan"
                  placeholder="/scan"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="jobs-endpoint">작업 관리 엔드포인트</Label>
                <Input 
                  id="jobs-endpoint" 
                  defaultValue="/jobs"
                  placeholder="/jobs"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="results-endpoint">결과 조회 엔드포인트</Label>
                <Input 
                  id="results-endpoint" 
                  defaultValue="/results"
                  placeholder="/results"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="config-endpoint">설정 관리 엔드포인트</Label>
                <Input 
                  id="config-endpoint" 
                  defaultValue="/database-configs"
                  placeholder="/database-configs"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="health-endpoint">헬스체크 엔드포인트</Label>
              <Input 
                id="health-endpoint" 
                defaultValue="/health"
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
      </div>
    </div>
  );
} 