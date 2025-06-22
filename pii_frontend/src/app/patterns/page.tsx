import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { 
  Search, 
  Filter, 
  Plus, 
  Edit, 
  Trash2, 
  Eye,
  Shield,
  AlertTriangle,
  CheckCircle,
  Clock,
  Database,
  FileText,
  User,
  CreditCard,
  Phone,
  Mail,
  MapPin,
  Hash,
  Calendar
} from "lucide-react";

export default function PatternsPage() {
  const patterns = [
    {
      id: 1,
      name: "이메일 주소",
      category: "연락처",
      pattern: "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b",
      riskLevel: "medium",
      description: "일반적인 이메일 주소 형식을 감지합니다",
      examples: ["user@example.com", "test.email@domain.co.kr"],
      detectionCount: 156,
      icon: Mail,
      color: "bg-blue-100 text-blue-800"
    },
    {
      id: 2,
      name: "전화번호",
      category: "연락처",
      pattern: "(\\+82|0)[0-9]{1,2}-?[0-9]{3,4}-?[0-9]{4}",
      riskLevel: "medium",
      description: "한국 전화번호 형식을 감지합니다",
      examples: ["010-1234-5678", "+82-10-1234-5678"],
      detectionCount: 89,
      icon: Phone,
      color: "bg-green-100 text-green-800"
    },
    {
      id: 3,
      name: "주민등록번호",
      category: "신원정보",
      pattern: "[0-9]{6}-[1-4][0-9]{6}",
      riskLevel: "high",
      description: "한국 주민등록번호 형식을 감지합니다",
      examples: ["123456-1234567", "123456-2345678"],
      detectionCount: 23,
      icon: User,
      color: "bg-red-100 text-red-800"
    },
    {
      id: 4,
      name: "신용카드번호",
      category: "금융정보",
      pattern: "\\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\\b",
      riskLevel: "high",
      description: "Visa, MasterCard, American Express 등 신용카드 번호를 감지합니다",
      examples: ["4111-1111-1111-1111", "5555-5555-5555-4444"],
      detectionCount: 12,
      icon: CreditCard,
      color: "bg-red-100 text-red-800"
    },
    {
      id: 5,
      name: "계좌번호",
      category: "금융정보",
      pattern: "\\b[0-9]{10,14}\\b",
      riskLevel: "medium",
      description: "은행 계좌번호 형식을 감지합니다",
      examples: ["123-456789-01-234", "123456789012"],
      detectionCount: 67,
      icon: Database,
      color: "bg-yellow-100 text-yellow-800"
    },
    {
      id: 6,
      name: "주소",
      category: "위치정보",
      pattern: "[가-힣]+시\\s*[가-힣]+구\\s*[가-힣]+동",
      riskLevel: "low",
      description: "한국 주소 형식을 감지합니다",
      examples: ["서울시 강남구 역삼동", "부산시 해운대구 우동"],
      detectionCount: 45,
      icon: MapPin,
      color: "bg-purple-100 text-purple-800"
    },
    {
      id: 7,
      name: "IP 주소",
      category: "네트워크",
      pattern: "\\b(?:[0-9]{1,3}\\.){3}[0-9]{1,3}\\b",
      riskLevel: "low",
      description: "IPv4 주소 형식을 감지합니다",
      examples: ["192.168.1.1", "10.0.0.1"],
      detectionCount: 34,
      icon: Hash,
      color: "bg-gray-100 text-gray-800"
    },
    {
      id: 8,
      name: "생년월일",
      category: "신원정보",
      pattern: "(19|20)[0-9]{2}-(0[1-9]|1[0-2])-(0[1-9]|[12][0-9]|3[01])",
      riskLevel: "medium",
      description: "생년월일 형식을 감지합니다",
      examples: ["1990-01-01", "2000-12-31"],
      detectionCount: 78,
      icon: Calendar,
      color: "bg-orange-100 text-orange-800"
    }
  ];

  const categories = ["전체", "연락처", "신원정보", "금융정보", "위치정보", "네트워크"];
  const riskLevels = ["전체", "high", "medium", "low"];

  return (
    <div className="flex-1 space-y-6 p-8 pt-6">
      <div className="flex items-center justify-between space-y-2">
        <h2 className="text-3xl font-bold tracking-tight">개인정보 패턴</h2>
        <div className="flex items-center space-x-2">
          <Button variant="outline">
            <Filter className="mr-2 h-4 w-4" />
            필터
          </Button>
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            새 패턴 추가
          </Button>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 패턴</CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{patterns.length}</div>
            <p className="text-xs text-muted-foreground">
              등록된 패턴 수
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">고위험 패턴</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">
              {patterns.filter(p => p.riskLevel === 'high').length}
            </div>
            <p className="text-xs text-muted-foreground">
              높은 위험도 패턴
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">총 감지 횟수</CardTitle>
            <Eye className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {patterns.reduce((sum, p) => sum + p.detectionCount, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              전체 감지된 개인정보
            </p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">활성 패턴</CardTitle>
            <CheckCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {patterns.filter(p => p.detectionCount > 0).length}
            </div>
            <p className="text-xs text-muted-foreground">
              감지된 패턴 수
            </p>
          </CardContent>
        </Card>
      </div>

      {/* 필터 및 검색 */}
      <Card>
        <CardHeader>
          <CardTitle>패턴 검색 및 필터</CardTitle>
          <CardDescription>
            개인정보 패턴을 검색하고 카테고리별로 필터링하세요
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center space-x-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="패턴 이름 또는 설명으로 검색..."
                className="pl-10"
              />
            </div>
            <select className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm">
              {categories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
            <select className="h-10 rounded-md border border-input bg-background px-3 py-2 text-sm">
              {riskLevels.map(level => (
                <option key={level} value={level}>
                  {level === 'high' ? '고위험' : 
                   level === 'medium' ? '중위험' : 
                   level === 'low' ? '저위험' : '전체'}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* 패턴 목록 */}
      <div className="grid gap-4">
        {patterns.map((pattern) => (
          <Card key={pattern.id} className="hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className={`p-2 rounded-lg ${pattern.color}`}>
                    <pattern.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <CardTitle className="text-lg">{pattern.name}</CardTitle>
                    <CardDescription className="flex items-center space-x-2 mt-1">
                      <Badge variant="outline">{pattern.category}</Badge>
                      <Badge 
                        variant={
                          pattern.riskLevel === 'high' ? 'destructive' :
                          pattern.riskLevel === 'medium' ? 'default' : 'secondary'
                        }
                      >
                        {pattern.riskLevel === 'high' ? '고위험' : 
                         pattern.riskLevel === 'medium' ? '중위험' : '저위험'}
                      </Badge>
                      <span className="text-sm text-muted-foreground">
                        감지: {pattern.detectionCount}회
                      </span>
                    </CardDescription>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button variant="outline" size="sm">
                    <Eye className="mr-1 h-4 w-4" />
                    상세보기
                  </Button>
                  <Button variant="outline" size="sm">
                    <Edit className="mr-1 h-4 w-4" />
                    편집
                  </Button>
                  <Button variant="outline" size="sm">
                    <Trash2 className="mr-1 h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <p className="text-sm text-muted-foreground">{pattern.description}</p>
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">정규표현식:</span>
                    <code className="text-xs bg-muted px-2 py-1 rounded">
                      {pattern.pattern}
                    </code>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">예시:</span>
                    <div className="flex space-x-2">
                      {pattern.examples.map((example, index) => (
                        <code key={index} className="text-xs bg-muted px-2 py-1 rounded">
                          {example}
                        </code>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
} 