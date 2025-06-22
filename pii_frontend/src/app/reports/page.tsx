import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  FileText, 
  Download, 
  Eye, 
  Calendar,
  AlertTriangle,
  CheckCircle,
  Clock
} from "lucide-react";

export default function ReportsPage() {
  return (
    <div className="flex-1 space-y-4 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">결과 리포트</h2>
        <div className="flex items-center space-x-2">
          <Button>새 리포트 생성</Button>
        </div>
      </div>
      
      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 리포트</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">18</div>
            <p className="text-xs text-muted-foreground">
              이번 달 생성된 리포트
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">고위험 발견</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">5</div>
            <p className="text-xs text-muted-foreground">
              고위험 개인정보 패턴
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평균 처리시간</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">45분</div>
            <p className="text-xs text-muted-foreground">
              스캔 완료까지 소요시간
            </p>
          </CardContent>
        </Card>
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>스캔 결과 리포트</CardTitle>
          <CardDescription>
            생성된 모든 스캔 결과 리포트를 확인하고 다운로드하세요
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {[
              {
                id: "report-001",
                name: "Production MySQL Database Scan Report",
                database: "MySQL",
                scanDate: "2024-01-15",
                status: "completed",
                riskLevel: "medium",
                findings: 23,
                fileSize: "2.3 MB"
              },
              {
                id: "report-002",
                name: "Oracle HR System Security Report",
                database: "Oracle",
                scanDate: "2024-01-14",
                status: "completed",
                riskLevel: "high",
                findings: 45,
                fileSize: "3.1 MB"
              },
              {
                id: "report-003",
                name: "Test Environment Scan Report",
                database: "PostgreSQL",
                scanDate: "2024-01-13",
                status: "completed",
                riskLevel: "low",
                findings: 8,
                fileSize: "1.2 MB"
              },
              {
                id: "report-004",
                name: "Development Database Analysis",
                database: "MySQL",
                scanDate: "2024-01-12",
                status: "completed",
                riskLevel: "medium",
                findings: 15,
                fileSize: "1.8 MB"
              }
            ].map((report) => (
              <div key={report.id} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h3 className="font-medium">{report.name}</h3>
                    <Badge variant={
                      report.riskLevel === 'high' ? 'destructive' :
                      report.riskLevel === 'medium' ? 'default' : 'secondary'
                    }>
                      {report.riskLevel === 'high' ? '고위험' :
                       report.riskLevel === 'medium' ? '중간위험' : '낮음위험'}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    {report.database} • {report.scanDate}
                  </p>
                </div>
                <div className="flex items-center space-x-2">
                  {report.status === 'completed' && (
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
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 