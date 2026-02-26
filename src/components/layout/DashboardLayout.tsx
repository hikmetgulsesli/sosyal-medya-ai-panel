import { ReactNode } from "react";
import { Sidebar } from "@/components/layout/Sidebar";

interface DashboardLayoutProps {
  children: ReactNode;
}

export function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-[var(--surface)] lg:pl-64">
      <Sidebar />
      <main className="pt-14 lg:pt-0">
        <div className="p-4 lg:p-8">{children}</div>
      </main>
    </div>
  );
}
