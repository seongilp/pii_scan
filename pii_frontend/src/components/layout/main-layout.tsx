import { Sidebar } from "./sidebar";
import { Header } from "./header";

interface MainLayoutProps {
  children: React.ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="flex h-screen bg-background">
      {/* 사이드바 - 15% 너비 */}
      <div 
        className="hidden border-r border-border/50 bg-sidebar lg:block"
        style={{ width: '15%' }}
      >
        <div className="flex h-full flex-col gap-2">
          <div className="flex-1 overflow-auto py-3">
            <Sidebar />
          </div>
        </div>
      </div>
      {/* 메인 콘텐츠 영역 - 85% 너비 */}
      <div 
        className="flex flex-col"
        style={{ width: '85%' }}
      >
        <Header />
        <main className="flex-1 overflow-auto bg-background">
          {children}
        </main>
      </div>
    </div>
  );
} 