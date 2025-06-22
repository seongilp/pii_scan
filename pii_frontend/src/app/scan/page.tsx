"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Database, Play, Settings, TestTube, CheckCircle, XCircle, Eye, EyeOff } from "lucide-react";
import { useState } from "react";

export default function ScanPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [noPassword, setNoPassword] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');

  const testConnection = async () => {
    setConnectionStatus('testing');
    // 실제로는 여기서 데이터베이스 연결을 테스트합니다
    setTimeout(() => {
      setConnectionStatus('success');
      setTimeout(() => setConnectionStatus('idle'), 2000);
    }, 1000);
  };

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">데이터베이스 스캔</h2>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Database className="h-5 w-5" />
              새 스캔 설정
            </CardTitle>
            <CardDescription>
              데이터베이스 연결 정보를 입력하고 스캔을 시작하세요
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="db-type">데이터베이스 유형</Label>
              <Select>
                <SelectTrigger>
                  <SelectValue placeholder="데이터베이스 유형 선택" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="mysql">MySQL</SelectItem>
                  <SelectItem value="oracle">Oracle</SelectItem>
                  <SelectItem value="postgresql">PostgreSQL</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="host">호스트</Label>
                <Input id="host" placeholder="localhost" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="port">포트</Label>
                <Input id="port" placeholder="3306" />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="database">데이터베이스명</Label>
              <Input id="database" placeholder="database_name" />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="username">사용자명</Label>
                <Input id="username" placeholder="username" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">비밀번호</Label>
                <div className="relative">
                  <Input 
                    id="password" 
                    type={showPassword ? "text" : "password"} 
                    placeholder="password"
                    disabled={noPassword}
                  />
                  <Button 
                    variant="ghost" 
                    size="icon" 
                    className="absolute right-0 top-0 h-full px-3"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={noPassword}
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Switch 
                id="no-password" 
                checked={noPassword}
                onCheckedChange={setNoPassword}
              />
              <Label htmlFor="no-password" className="text-sm">
                패스워드 없음 (인증 없음)
              </Label>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="sample-size">샘플 크기</Label>
              <Input id="sample-size" placeholder="100" />
            </div>

            <div className="flex items-center space-x-4">
              <Button 
                variant="outline" 
                onClick={testConnection}
                disabled={connectionStatus === 'testing'}
              >
                {connectionStatus === 'testing' ? (
                  <>
                    <TestTube className="mr-2 h-4 w-4 animate-spin" />
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
            
            <div className="flex space-x-2">
              <Button className="flex-1">
                <Play className="mr-2 h-4 w-4" />
                스캔 시작
              </Button>
              <Button variant="outline">
                <Settings className="mr-2 h-4 w-4" />
                고급 설정
              </Button>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>저장된 설정</CardTitle>
            <CardDescription>
              이전에 사용한 데이터베이스 설정들
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {[
                { name: "Production MySQL", host: "prod-db.company.com", type: "MySQL" },
                { name: "Development Oracle", host: "dev-oracle.company.com", type: "Oracle" },
                { name: "Test PostgreSQL", host: "test-pg.company.com", type: "PostgreSQL" },
              ].map((config, i) => (
                <div key={i} className="flex items-center justify-between p-3 border rounded-lg">
                  <div>
                    <p className="font-medium">{config.name}</p>
                    <p className="text-sm text-muted-foreground">{config.host} ({config.type})</p>
                  </div>
                  <Button variant="outline" size="sm">
                    사용
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 