"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Database, Play, Settings, TestTube, CheckCircle, XCircle, Eye, EyeOff, Info } from "lucide-react";
import { useState, useEffect } from "react";

const API_URL = typeof window !== "undefined" && localStorage.getItem("api-config")
  ? JSON.parse(localStorage.getItem("api-config") || '{}').baseUrl || 'http://localhost:18000'
  : 'http://localhost:18000';
const API_TOKEN = typeof window !== "undefined" && localStorage.getItem("api-config")
  ? JSON.parse(localStorage.getItem("api-config") || '{}').token || 'your-secret-token'
  : 'your-secret-token';

export default function ScanPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [noPassword, setNoPassword] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle');
  const [connectionMessage, setConnectionMessage] = useState<string>("");
  const [cron, setCron] = useState("");
  const [form, setForm] = useState({
    name: "",
    db_type: "mysql",
    host: "",
    port: 3306,
    database: "",
    service_name: "",
    user: "",
    password: "",
    sample_size: 100,
  });
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [saveMessage, setSaveMessage] = useState<string>("");
  const [savedConfigs, setSavedConfigs] = useState<any[]>([]);
  const [savedLoading, setSavedLoading] = useState(false);
  const [savedError, setSavedError] = useState<string>("");
  const [editId, setEditId] = useState<number|null>(null);

  // 목록 새로고침 함수 분리
  const fetchConfigs = async () => {
    setSavedLoading(true);
    setSavedError("");
    try {
      const res = await fetch(`${API_URL}/database-configs`, {
        headers: {
          "Authorization": `Bearer ${API_TOKEN}`,
        },
      });
      if (res.ok) {
        const data = await res.json();
        setSavedConfigs(data);
      } else {
        const err = await res.json();
        setSavedError(err.detail || '불러오기 실패');
      }
    } catch (e: any) {
      setSavedError(e.message || '불러오기 실패');
    } finally {
      setSavedLoading(false);
    }
  };

  useEffect(() => {
    fetchConfigs();
  }, []);

  const handleUseConfig = (config: any) => {
    setForm(f => ({
      ...f,
      name: config.name || "",
      db_type: config.db_type || "mysql",
      host: config.host || "",
      port: config.port || 3306,
      database: config.database || "",
      service_name: config.service_name || "",
      user: config.user || "",
      password: config.password || "",
      sample_size: config.sample_size || 100,
    }));
    setEditId(null);
  };

  const handleEditConfig = (config: any) => {
    setForm(f => ({
      ...f,
      name: config.name || "",
      db_type: config.db_type || "mysql",
      host: config.host || "",
      port: config.port || 3306,
      database: config.database || "",
      service_name: config.service_name || "",
      user: config.user || "",
      password: config.password || "",
      sample_size: config.sample_size || 100,
    }));
    setEditId(config.id);
  };

  const handleDeleteConfig = async (id: number) => {
    if (!window.confirm('정말 삭제하시겠습니까?')) return;
    try {
      const res = await fetch(`${API_URL}/database-configs/${id}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${API_TOKEN}`,
        },
      });
      if (res.ok) {
        fetchConfigs();
      } else {
        const err = await res.json();
        alert(err.detail || '삭제 실패');
      }
    } catch (e: any) {
      alert(e.message || '삭제 실패');
    }
  };

  const testConnection = async () => {
    setConnectionStatus('testing');
    setConnectionMessage("");
    try {
      const body = {
        ...form,
        password: noPassword ? "" : form.password,
        port: Number(form.port),
        sample_size: Number(form.sample_size),
      };
      const res = await fetch(`${API_URL}/test-connection`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${API_TOKEN}`,
        },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (data.success) {
        setConnectionStatus('success');
        setConnectionMessage(data.message || "연결 성공!");
        setTimeout(() => setConnectionStatus('idle'), 2000);
      } else {
        setConnectionStatus('error');
        setConnectionMessage(data.message || "연결 실패");
      }
    } catch (e: any) {
      setConnectionStatus('error');
      setConnectionMessage(e.message || "연결 실패");
    }
  };

  const saveConfig = async () => {
    setSaveStatus('saving');
    setSaveMessage("");
    try {
      const body = {
        ...form,
        port: Number(form.port),
        sample_size: Number(form.sample_size),
        password: noPassword ? "" : form.password,
      };
      let res;
      if (editId) {
        res = await fetch(`${API_URL}/database-configs/${editId}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${API_TOKEN}`,
          },
          body: JSON.stringify(body),
        });
      } else {
        res = await fetch(`${API_URL}/database-configs`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${API_TOKEN}`,
          },
          body: JSON.stringify(body),
        });
      }
      if (res.ok) {
        const data = await res.json();
        setSaveStatus('success');
        setSaveMessage(`${editId ? '수정' : '저장'} 성공: ${data.name || '설정'}`);
        setEditId(null);
        fetchConfigs();
        setTimeout(() => setSaveStatus('idle'), 2000);
      } else {
        const err = await res.json();
        setSaveStatus('error');
        setSaveMessage(err.detail || (editId ? '수정 실패' : '저장 실패'));
      }
    } catch (e: any) {
      setSaveStatus('error');
      setSaveMessage(e.message || (editId ? '수정 실패' : '저장 실패'));
    }
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
              <Label htmlFor="config-name">설정 이름</Label>
              <Input id="config-name" placeholder="예: 운영 MySQL" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="db-type">데이터베이스 유형</Label>
              <Select value={form.db_type} onValueChange={v => setForm(f => ({ ...f, db_type: v }))}>
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
                <Input id="host" placeholder="localhost" value={form.host} onChange={e => setForm(f => ({ ...f, host: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="port">포트</Label>
                <Input id="port" placeholder="3306" value={form.port} onChange={e => setForm(f => ({ ...f, port: Number(e.target.value) }))} />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="database">데이터베이스명</Label>
              <Input id="database" placeholder="database_name" value={form.database} onChange={e => setForm(f => ({ ...f, database: e.target.value }))} />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="username">사용자명</Label>
                <Input id="username" placeholder="username" value={form.user} onChange={e => setForm(f => ({ ...f, user: e.target.value }))} />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">비밀번호</Label>
                <div className="relative">
                  <Input 
                    id="password" 
                    type={showPassword ? "text" : "password"} 
                    placeholder="password"
                    disabled={noPassword}
                    value={form.password}
                    onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
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
              <Input id="sample-size" placeholder="100" value={form.sample_size} onChange={e => setForm(f => ({ ...f, sample_size: Number(e.target.value) }))} />
            </div>

            {/* 스캔 주기 (cron) 입력 */}
            <div className="space-y-2">
              <Label htmlFor="scan-cron">스캔 주기 (cron)</Label>
              <Input
                id="scan-cron"
                placeholder="0 0 * * *"
                value={cron}
                onChange={e => setCron(e.target.value)}
              />
              <div className="flex items-start text-xs text-muted-foreground gap-2 mt-1">
                <Info className="h-4 w-4 mt-0.5" />
                <span>
                  예시: <code>0 0 * * * (매일 0시)</code>, <code>0 */6 * * * (6시간마다)</code>, <code>30 9 * * 1-5 (평일 오전 9:30)</code><br/>
                  <span className="text-[11px]">cron 형식: 분 시 일 월 요일</span>
                </span>
              </div>
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
                  <span className="text-sm">{connectionMessage || "연결 성공!"}</span>
                </div>
              )}
              
              {connectionStatus === 'error' && (
                <div className="flex items-center space-x-2 text-red-600">
                  <XCircle className="h-4 w-4" />
                  <span className="text-sm">{connectionMessage || "연결 실패"}</span>
                </div>
              )}
            </div>
            
            <div className="flex space-x-2">
              <Button className="flex-1">
                <Play className="mr-2 h-4 w-4" />
                스캔 시작
              </Button>
              <Button variant="outline" className="flex-1" onClick={saveConfig} disabled={saveStatus === 'saving'}>
                <Settings className="mr-2 h-4 w-4" />
                {saveStatus === 'saving' ? (editId ? '수정 중...' : '저장 중...') : (editId ? '수정 저장' : '스캔 저장')}
              </Button>
              <Button variant="outline">
                <Settings className="mr-2 h-4 w-4" />
                고급 설정
              </Button>
            </div>

            {saveStatus === 'success' && (
              <div className="flex items-center space-x-2 text-green-600 mt-2">
                <CheckCircle className="h-4 w-4" />
                <span className="text-sm">{saveMessage}</span>
              </div>
            )}
            {saveStatus === 'error' && (
              <div className="flex items-center space-x-2 text-red-600 mt-2">
                <XCircle className="h-4 w-4" />
                <span className="text-sm">{saveMessage}</span>
              </div>
            )}
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
              {savedLoading ? (
                <div className="text-muted-foreground text-sm">불러오는 중...</div>
              ) : savedError ? (
                <div className="text-red-600 text-sm">{savedError}</div>
              ) : savedConfigs.length === 0 ? (
                <div className="text-muted-foreground text-sm">저장된 설정이 없습니다.</div>
              ) : (
                savedConfigs.map((config, i) => (
                  <div key={config.id || i} className="flex items-center justify-between p-3 border rounded-lg">
                    <div>
                      <p className="font-medium">{config.name}</p>
                      <p className="text-sm text-muted-foreground">{config.host} ({config.db_type})</p>
                    </div>
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleUseConfig(config)}>
                        사용
                      </Button>
                      <Button variant="secondary" size="sm" onClick={() => handleEditConfig(config)}>
                        수정
                      </Button>
                      <Button variant="destructive" size="sm" onClick={() => handleDeleteConfig(config.id)}>
                        삭제
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
} 