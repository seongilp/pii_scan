"use client";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Database,
  FileText,
  Home,
  Settings,
  Shield,
  BarChart3,
  Activity,
  Users,
  AlertTriangle,
  CheckCircle,
  Clock,
  Play,
  StopCircle,
  Download,
  Plus,
  Search
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

interface SidebarProps extends React.HTMLAttributes<HTMLDivElement> {}

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname();

  const navigation = [
    {
      title: "대시보드",
      href: "/",
      icon: Home,
      variant: "default" as const,
    },
    {
      title: "데이터베이스 스캔",
      href: "/scan",
      icon: Database,
      variant: "default" as const,
    },
    {
      title: "스캔 작업 관리",
      href: "/jobs",
      icon: Activity,
      variant: "default" as const,
    },
    {
      title: "결과 리포트",
      href: "/reports",
      icon: FileText,
      variant: "default" as const,
    },
    {
      title: "개인정보 패턴",
      href: "/patterns",
      icon: Shield,
      variant: "default" as const,
    },
    {
      title: "통계 분석",
      href: "/analytics",
      icon: BarChart3,
      variant: "default" as const,
    },
    {
      title: "설정",
      href: "/settings",
      icon: Settings,
      variant: "default" as const,
    },
  ];

  return (
    <div className={cn("pb-12", className)}>
      <div className="space-y-5 py-5">
        <div className="px-5 py-4">
          <h2 className="mb-5 px-4 text-xl font-semibold tracking-tight" style={{ color: '#1e3a8a' }}>
            DB PII Scanner
          </h2>
          <div className="space-y-3">
            {navigation.map((item) => (
              <Link key={item.href} href={item.href}>
                <Button
                  variant="ghost"
                  className={cn(
                    "w-full justify-start transition-all duration-200",
                    pathname === item.href 
                      ? "shadow-sm" 
                      : "hover:bg-gray-100/50 text-gray-600 hover:text-gray-900"
                  )}
                  style={{
                    backgroundColor: pathname === item.href ? '#dbeafe' : 'transparent',
                    color: pathname === item.href ? '#1e3a8a' : undefined,
                    borderRight: pathname === item.href ? '3px solid #1e3a8a' : 'none',
                    fontSize: '16px',
                    padding: '14px 16px',
                    fontWeight: '500',
                  }}
                  size="default"
                >
                  <item.icon 
                    className="mr-4 h-6 w-6 transition-colors"
                    style={{ 
                      color: pathname === item.href ? '#1e3a8a' : '#6b7280' 
                    }}
                  />
                  {item.title}
                </Button>
              </Link>
            ))}
          </div>
        </div>
        <Separator className="bg-gray-200" />
        <div className="px-5 py-4">
          <h3 className="mb-4 px-4 text-base font-medium text-gray-500">빠른 액션</h3>
          <div className="space-y-3">
            <Button 
              variant="outline" 
              className="w-full justify-start transition-all duration-200"
              style={{
                borderColor: '#bfdbfe',
                color: '#6b7280',
                fontSize: '15px',
                padding: '12px 16px',
                fontWeight: '500',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#dbeafe';
                e.currentTarget.style.borderColor = '#3b82f6';
                e.currentTarget.style.color = '#1e3a8a';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.borderColor = '#bfdbfe';
                e.currentTarget.style.color = '#6b7280';
              }}
            >
              <Plus className="mr-4 h-5 w-5" />
              새 스캔 시작
            </Button>
            <Button 
              variant="outline" 
              className="w-full justify-start transition-all duration-200"
              style={{
                borderColor: '#bfdbfe',
                color: '#6b7280',
                fontSize: '15px',
                padding: '12px 16px',
                fontWeight: '500',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#dbeafe';
                e.currentTarget.style.borderColor = '#3b82f6';
                e.currentTarget.style.color = '#1e3a8a';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'transparent';
                e.currentTarget.style.borderColor = '#bfdbfe';
                e.currentTarget.style.color = '#6b7280';
              }}
            >
              <Search className="mr-4 h-5 w-5" />
              스캔 검색
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
} 