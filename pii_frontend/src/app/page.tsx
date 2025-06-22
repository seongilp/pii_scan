"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Database, 
  FileText, 
  Shield, 
  Activity,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Clock
} from "lucide-react";
import { useEffect, useState } from "react";
import { getApiClient } from "@/lib/api";

interface DashboardData {
  stats: {
    total_jobs: number;
    completed_jobs: number;
    running_jobs: number;
    high_risk_patterns: number;
  };
  recent_jobs: Array<{
    id: string;
    name: string;
    status: string;
    database: string;
    host: string;
    created_at: string;
    progress: number;
  }>;
  pattern_distribution: Record<string, number>;
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const client = getApiClient();
      const result = await client.getDashboard();

      if ((result.success && result.data) || (typeof result === "object" && result !== null && "stats" in result)) {
        setData(result.data || result);
        setError(null);
      } else {
        setError(result.error || '데이터를 불러올 수 없습니다');
      }
    } catch (err) {
      setError('서버 연결에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">데이터를 불러오는 중...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 space-y-4 p-8 pt-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={loadDashboardData}>다시 시도</Button>
          </div>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">대시보드</h2>
        <div className="flex items-center space-x-2">
          <Button onClick={loadDashboardData}>새로고침</Button>
        </div>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 스캔 작업</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.stats.total_jobs}</div>
            <p className="text-xs text-muted-foreground">
              전체 스캔 작업 수
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">완료된 스캔</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.stats.completed_jobs}</div>
            <p className="text-xs text-muted-foreground">
              성공적으로 완료된 작업
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">진행 중</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.stats.running_jobs}</div>
            <p className="text-xs text-muted-foreground">
              현재 실행 중인 작업
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">고위험 패턴</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{data.stats.high_risk_patterns}</div>
            <p className="text-xs text-muted-foreground">
              발견된 고위험 패턴
            </p>
          </CardContent>
        </Card>
      </div>
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>최근 스캔 작업</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {data.recent_jobs.map((job) => (
                <div key={job.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium">{job.name}</h3>
                      <Badge variant={
                        job.status === 'completed' ? 'default' :
                        job.status === 'running' ? 'secondary' :
                        job.status === 'pending' ? 'outline' : 'destructive'
                      }>
                        {job.status === 'completed' ? '완료' :
                         job.status === 'running' ? '진행중' :
                         job.status === 'pending' ? '대기중' : '실패'}
                      </Badge>
                      <Badge variant="outline">{job.database}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {job.host} • {new Date(job.created_at).toLocaleString('ko-KR')}
                    </p>
                    {job.status === 'running' && (
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                            style={{ width: `${job.progress}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-muted-foreground mt-1">{job.progress}% 완료</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>개인정보 패턴 분포</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(data.pattern_distribution).map(([pattern, count]) => (
                <div key={pattern} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">{pattern}</span>
                    <span className="text-sm text-muted-foreground">{count}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${(count / Math.max(...Object.values(data.pattern_distribution))) * 100}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
