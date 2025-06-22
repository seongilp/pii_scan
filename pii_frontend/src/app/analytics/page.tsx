"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { 
  BarChart3, 
  TrendingUp, 
  TrendingDown,
  Activity,
  Database,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Calendar,
  Download,
  Filter,
  RefreshCw
} from "lucide-react";
import { useState, useEffect } from "react";

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState("30");
  const [selectedDatabase, setSelectedDatabase] = useState("all");
  const [isLoading, setIsLoading] = useState(false);

  // 더미 데이터 (실제로는 API에서 가져옴)
  const analyticsData = {
    overview: {
      totalScans: 156,
      completedScans: 142,
      failedScans: 8,
      runningScans: 6,
      successRate: 91.0,
      totalPatterns: 24,
      activePatterns: 22,
      highRiskFindings: 45
    },
    trends: {
      daily: [
        { date: "2024-01-10", scans: 12, findings: 89 },
        { date: "2024-01-11", scans: 15, findings: 123 },
        { date: "2024-01-12", scans: 8, findings: 67 },
        { date: "2024-01-13", scans: 20, findings: 156 },
        { date: "2024-01-14", scans: 18, findings: 134 },
        { date: "2024-01-15", scans: 25, findings: 189 },
        { date: "2024-01-16", scans: 22, findings: 167 }
      ],
      monthly: [
        { month: "2023-08", scans: 45, findings: 234 },
        { month: "2023-09", scans: 52, findings: 289 },
        { month: "2023-10", scans: 48, findings: 267 },
        { month: "2023-11", scans: 61, findings: 345 },
        { month: "2023-12", scans: 58, findings: 312 },
        { month: "2024-01", scans: 67, findings: 378 }
      ]
    },
    databaseStats: {
      mysql: { total: 89, completed: 82, failed: 4, running: 3 },
      oracle: { total: 45, completed: 41, failed: 2, running: 2 },
      postgresql: { total: 22, completed: 19, failed: 2, running: 1 }
    },
    patternStats: {
      "이메일 주소": { count: 156, risk: "medium", trend: "up" },
      "전화번호": { count: 89, risk: "medium", trend: "down" },
      "주민등록번호": { count: 23, risk: "high", trend: "stable" },
      "신용카드번호": { count: 12, risk: "high", trend: "up" },
      "계좌번호": { count: 67, risk: "medium", trend: "down" },
      "IP 주소": { count: 34, risk: "low", trend: "stable" },
      "생년월일": { count: 78, risk: "medium", trend: "up" }
    },
    riskAnalysis: {
      high: { count: 45, percentage: 12.3 },
      medium: { count: 234, percentage: 64.1 },
      low: { count: 87, percentage: 23.6 }
    }
  };

  const refreshData = async () => {
    setIsLoading(true);
    // 실제로는 API 호출
    await new Promise(resolve => setTimeout(resolve, 1000));
    setIsLoading(false);
  };

  useEffect(() => {
    refreshData();
  }, [timeRange, selectedDatabase]);

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">통계 분석</h2>
        <div className="flex items-center space-x-2">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7">최근 7일</SelectItem>
              <SelectItem value="30">최근 30일</SelectItem>
              <SelectItem value="90">최근 90일</SelectItem>
              <SelectItem value="365">최근 1년</SelectItem>
            </SelectContent>
          </Select>
          <Select value={selectedDatabase} onValueChange={setSelectedDatabase}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">모든 데이터베이스</SelectItem>
              <SelectItem value="mysql">MySQL</SelectItem>
              <SelectItem value="oracle">Oracle</SelectItem>
              <SelectItem value="postgresql">PostgreSQL</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={refreshData} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            새로고침
          </Button>
          <Button>
            <Download className="mr-2 h-4 w-4" />
            보고서 다운로드
          </Button>
        </div>
      </div>

      {/* 개요 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 스캔 작업</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.overview.totalScans}</div>
            <p className="text-xs text-muted-foreground">
              +12 from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">성공률</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.overview.successRate}%</div>
            <p className="text-xs text-muted-foreground">
              +2.1% from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">고위험 발견</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{analyticsData.overview.highRiskFindings}</div>
            <p className="text-xs text-muted-foreground">
              -5 from last month
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">활성 패턴</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{analyticsData.overview.activePatterns}</div>
            <p className="text-xs text-muted-foreground">
              +3 from last month
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        {/* 트렌드 차트 */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>스캔 트렌드</CardTitle>
            <CardDescription>
              일별 스캔 작업 및 개인정보 발견 추이
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {analyticsData.trends.daily.map((day, index) => (
                <div key={day.date} className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <div className="w-20 text-sm text-muted-foreground">
                      {new Date(day.date).toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <div className="text-sm font-medium">스캔: {day.scans}</div>
                        <div className="text-sm text-muted-foreground">발견: {day.findings}</div>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${(day.scans / 25) * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-1">
                    {day.scans > (analyticsData.trends.daily[index - 1]?.scans || 0) ? (
                      <TrendingUp className="h-4 w-4 text-green-600" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-red-600" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 데이터베이스별 통계 */}
        <Card className="col-span-3">
          <CardHeader>
            <CardTitle>데이터베이스별 통계</CardTitle>
            <CardDescription>
              데이터베이스 유형별 스캔 결과
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(analyticsData.databaseStats).map(([db, stats]) => (
                <div key={db} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium capitalize">{db}</span>
                    <Badge variant="outline">{stats.total}개</Badge>
                  </div>
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span>완료</span>
                      <span className="text-green-600">{stats.completed}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span>실패</span>
                      <span className="text-red-600">{stats.failed}</span>
                    </div>
                    <div className="flex justify-between text-xs">
                      <span>진행중</span>
                      <span className="text-blue-600">{stats.running}</span>
                    </div>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-1">
                    <div 
                      className="bg-green-600 h-1 rounded-full" 
                      style={{ width: `${(stats.completed / stats.total) * 100}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* 개인정보 패턴 통계 */}
        <Card>
          <CardHeader>
            <CardTitle>개인정보 패턴 통계</CardTitle>
            <CardDescription>
              패턴별 발견 횟수 및 위험도 분석
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(analyticsData.patternStats).map(([pattern, stats]) => (
                <div key={pattern} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${
                      stats.risk === 'high' ? 'bg-red-500' :
                      stats.risk === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                    }`}></div>
                    <div>
                      <p className="font-medium">{pattern}</p>
                      <p className="text-sm text-muted-foreground">
                        {stats.count}회 발견
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {stats.trend === 'up' && <TrendingUp className="h-4 w-4 text-green-600" />}
                    {stats.trend === 'down' && <TrendingDown className="h-4 w-4 text-red-600" />}
                    {stats.trend === 'stable' && <div className="w-4 h-4 text-gray-400">—</div>}
                    <Badge variant={
                      stats.risk === 'high' ? 'destructive' :
                      stats.risk === 'medium' ? 'default' : 'secondary'
                    }>
                      {stats.risk === 'high' ? '고위험' : 
                       stats.risk === 'medium' ? '중위험' : '저위험'}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* 위험도 분석 */}
        <Card>
          <CardHeader>
            <CardTitle>위험도 분석</CardTitle>
            <CardDescription>
              발견된 개인정보의 위험도 분포
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(analyticsData.riskAnalysis).map(([risk, data]) => (
                <div key={risk} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className={`w-3 h-3 rounded-full ${
                        risk === 'high' ? 'bg-red-500' :
                        risk === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                      }`}></div>
                      <span className="text-sm font-medium">
                        {risk === 'high' ? '고위험' : 
                         risk === 'medium' ? '중위험' : '저위험'}
                      </span>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {data.count}개 ({data.percentage}%)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full ${
                        risk === 'high' ? 'bg-red-500' :
                        risk === 'medium' ? 'bg-yellow-500' : 'bg-green-500'
                      }`}
                      style={{ width: `${data.percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 월별 트렌드 */}
      <Card>
        <CardHeader>
          <CardTitle>월별 트렌드</CardTitle>
          <CardDescription>
            월별 스캔 작업 및 개인정보 발견 추이
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-6 gap-4">
            {analyticsData.trends.monthly.map((month) => (
              <div key={month.month} className="text-center space-y-2">
                <div className="text-sm font-medium">
                  {new Date(month.month + '-01').toLocaleDateString('ko-KR', { month: 'short' })}
                </div>
                <div className="text-2xl font-bold">{month.scans}</div>
                <div className="text-xs text-muted-foreground">
                  {month.findings}개 발견
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1">
                  <div 
                    className="bg-blue-600 h-1 rounded-full" 
                    style={{ width: `${(month.scans / 67) * 100}%` }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 