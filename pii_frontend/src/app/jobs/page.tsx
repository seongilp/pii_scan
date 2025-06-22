import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  Search, 
  Filter, 
  Play, 
  StopCircle, 
  Download,
  Eye,
  Trash2
} from "lucide-react";

export default function JobsPage() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">스캔 작업 관리</h2>
        <div className="flex items-center space-x-2">
          <Button>새 작업 시작</Button>
        </div>
      </div>
      
      <div className="flex items-center space-x-2">
        <div className="relative flex-1">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input placeholder="작업 검색..." className="pl-8" />
        </div>
        <Button variant="outline">
          <Filter className="mr-2 h-4 w-4" />
          필터
        </Button>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>스캔 작업 목록</CardTitle>
          <CardDescription>
            모든 스캔 작업의 상태와 진행 상황을 확인하세요
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              {
                id: "job-001",
                name: "Production MySQL Database Scan",
                database: "MySQL",
                host: "prod-db.company.com",
                status: "completed",
                progress: 100,
                startTime: "2024-01-15 10:30",
                endTime: "2024-01-15 11:45",
                riskLevel: "medium"
              },
              {
                id: "job-002",
                name: "Oracle HR System Scan",
                database: "Oracle",
                host: "hr-oracle.company.com",
                status: "running",
                progress: 65,
                startTime: "2024-01-15 14:20",
                endTime: null,
                riskLevel: "high"
              },
              {
                id: "job-003",
                name: "Test PostgreSQL Analytics",
                database: "PostgreSQL",
                host: "test-pg.company.com",
                status: "pending",
                progress: 0,
                startTime: null,
                endTime: null,
                riskLevel: "low"
              },
              {
                id: "job-004",
                name: "Development Database Scan",
                database: "MySQL",
                host: "dev-db.company.com",
                status: "failed",
                progress: 30,
                startTime: "2024-01-14 16:00",
                endTime: "2024-01-14 16:15",
                riskLevel: "low"
              }
            ].map((job) => (
              <div key={job.id} className="flex items-center justify-between p-4 border rounded-lg">
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
                    {job.host} • {job.startTime}
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
                <div className="flex items-center space-x-2">
                  {job.status === 'completed' && (
                    <>
                      <Button variant="outline" size="sm">
                        <Eye className="mr-1 h-4 w-4" />
                        결과 보기
                      </Button>
                      <Button variant="outline" size="sm">
                        <Download className="mr-1 h-4 w-4" />
                        다운로드
                      </Button>
                    </>
                  )}
                  {job.status === 'running' && (
                    <Button variant="outline" size="sm">
                      <StopCircle className="mr-1 h-4 w-4" />
                      중지
                    </Button>
                  )}
                  {job.status === 'pending' && (
                    <Button variant="outline" size="sm">
                      <Play className="mr-1 h-4 w-4" />
                      시작
                    </Button>
                  )}
                  <Button variant="outline" size="sm">
                    <Trash2 className="mr-1 h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 