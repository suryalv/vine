import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { ThemeService } from './services/theme.service';
import { DashboardComponent } from './views/dashboard/dashboard.component';
import { DocumentsComponent } from './views/documents/documents.component';
import { ChatComponent } from './views/chat/chat.component';
import { AnalyticsComponent } from './views/analytics/analytics.component';

type View = 'dashboard' | 'documents' | 'chat' | 'analytics';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    LucideAngularModule,
    DashboardComponent,
    DocumentsComponent,
    ChatComponent,
    AnalyticsComponent,
  ],
  template: `
    <div class="app-shell">

      <!-- Sidebar -->
      <aside class="sidebar">
        <!-- AIG Logo — clean text mark -->
        <div class="logo-box">
          <span class="logo-text">AIG</span>
        </div>

        <!-- Nav -->
        <nav class="nav">
          <button
            *ngFor="let item of navItems"
            class="nav-btn"
            [class.active]="activeView === item.view"
            (click)="activeView = item.view"
            [title]="item.label"
          >
            <lucide-icon [name]="item.icon" [size]="20"></lucide-icon>
            <div *ngIf="activeView === item.view" class="nav-indicator"></div>
          </button>
        </nav>

        <!-- Footer -->
        <div class="sidebar-foot">
          <button class="theme-btn" (click)="themeService.toggle()" [title]="themeService.theme() === 'dark' ? 'Light mode' : 'Dark mode'">
            <span *ngIf="themeService.theme() === 'dark'">&#9728;</span>
            <span *ngIf="themeService.theme() === 'light'">&#9790;</span>
          </button>
          <div class="online-dot"><div class="dot-inner"></div></div>
          <div class="avatar">FX</div>
        </div>
      </aside>

      <!-- Main Area -->
      <main class="main">
        <!-- Top Bar -->
        <header class="topbar">
          <div class="topbar-left">
            <h1 class="page-title">{{ currentTitle }}</h1>
            <span class="page-sub">{{ currentSub }}</span>
          </div>
          <div class="topbar-right">
            <div class="agent-badge">
              <div class="agent-dot-a">B</div>
              <div class="agent-dot-b">C</div>
              <span class="agent-label">AI Active</span>
            </div>
            <button class="topbar-btn">Export</button>
          </div>
        </header>

        <!-- View Content -->
        <div class="content custom-scrollbar">
          <app-dashboard *ngIf="activeView === 'dashboard'"></app-dashboard>
          <app-documents *ngIf="activeView === 'documents'"></app-documents>
          <app-chat *ngIf="activeView === 'chat'"></app-chat>
          <app-analytics *ngIf="activeView === 'analytics'"></app-analytics>
        </div>
      </main>
    </div>
  `,
  styles: [`
    :host { display: block; height: 100vh; width: 100vw; }
    .app-shell {
      display: flex;
      height: 100%;
      width: 100%;
      background: var(--bg);
      color: var(--text-primary);
      overflow: hidden;
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ===== Sidebar ===== */
    .sidebar {
      width: 4.5rem;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.25rem 0;
      border-right: 1px solid var(--border);
      background: var(--sidebar-bg);
      z-index: 50;
      flex-shrink: 0;
    }
    .logo-box {
      width: 2.75rem;
      height: 1.75rem;
      border-radius: 0.5rem;
      background: var(--accent);
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 2rem;
      box-shadow: 0 2px 12px var(--accent-shadow);
    }
    .logo-text {
      font-size: 0.8rem;
      font-weight: 900;
      color: white;
      letter-spacing: 0.08em;
      font-family: 'Inter', sans-serif;
    }

    .nav { display: flex; flex-direction: column; gap: 0.25rem; }
    .nav-btn {
      position: relative;
      width: 2.75rem;
      height: 2.75rem;
      border-radius: 0.75rem;
      border: none;
      background: transparent;
      color: var(--nav-icon);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }
    .nav-btn:hover { color: var(--nav-icon-hover); background: var(--nav-active-bg); }
    .nav-btn.active { color: var(--accent); background: var(--nav-active-bg); }
    .nav-indicator {
      position: absolute;
      right: -14px;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 1.25rem;
      background: var(--accent);
      border-radius: 3px 0 0 3px;
      box-shadow: 0 0 8px var(--accent-shadow);
    }

    .sidebar-foot {
      margin-top: auto;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 0.875rem;
    }
    .theme-btn {
      width: 2.25rem;
      height: 2.25rem;
      border-radius: 0.625rem;
      border: 1px solid var(--border);
      background: transparent;
      color: var(--text-muted);
      cursor: pointer;
      font-size: 0.9rem;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: all 0.2s;
    }
    .theme-btn:hover { border-color: var(--accent-muted); color: var(--accent); }
    .online-dot {
      width: 1.75rem;
      height: 1.75rem;
      border-radius: 50%;
      border: 1px solid rgba(16,185,129,0.35);
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .dot-inner { width: 0.45rem; height: 0.45rem; border-radius: 50%; background: #10b981; animation: pulse 2s infinite; }
    .avatar {
      width: 2.25rem;
      height: 2.25rem;
      border-radius: 0.625rem;
      background: var(--accent-bg);
      color: var(--accent);
      font-size: 0.65rem;
      font-weight: 800;
      display: flex;
      align-items: center;
      justify-content: center;
      letter-spacing: 0.05em;
    }

    /* ===== Main ===== */
    .main {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .topbar {
      height: 3.5rem;
      padding: 0 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--border);
      background: var(--sidebar-bg);
      flex-shrink: 0;
    }
    .topbar-left { display: flex; align-items: baseline; gap: 0.75rem; }
    .page-title {
      font-size: 0.85rem;
      font-weight: 700;
      color: var(--text-primary);
    }
    .page-sub {
      font-size: 0.65rem;
      font-weight: 500;
      color: var(--text-muted);
    }
    .topbar-right { display: flex; align-items: center; gap: 1rem; }
    .agent-badge {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      background: var(--accent-bg);
      border: 1px solid var(--accent-muted);
    }
    .agent-dot-a, .agent-dot-b {
      width: 1.125rem;
      height: 1.125rem;
      border-radius: 50%;
      font-size: 0.5rem;
      font-weight: 800;
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .agent-dot-a { background: var(--accent); margin-right: -0.375rem; }
    .agent-dot-b { background: #06b6d4; }
    .agent-label {
      font-size: 0.6rem;
      font-weight: 700;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .topbar-btn {
      font-size: 0.65rem;
      font-weight: 700;
      color: var(--text-muted);
      background: var(--chip-bg);
      border: 1px solid var(--border);
      border-radius: 0.5rem;
      padding: 0.35rem 0.75rem;
      cursor: pointer;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      transition: all 0.2s;
    }
    .topbar-btn:hover { color: var(--accent); border-color: var(--accent-muted); }

    .content {
      flex: 1;
      overflow-y: auto;
      padding: 1.5rem;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.35; }
    }
  `]
})
export class AppComponent {
  themeService = inject(ThemeService);
  activeView: View = 'dashboard';

  navItems: { view: View; icon: string; label: string }[] = [
    { view: 'dashboard', icon: 'activity', label: 'Dashboard' },
    { view: 'documents', icon: 'file-text', label: 'Documents' },
    { view: 'chat', icon: 'sparkles', label: 'AI Chat' },
    { view: 'analytics', icon: 'layers', label: 'Analytics' },
  ];

  get currentTitle(): string {
    const map: Record<View, string> = {
      dashboard: 'Underwriting Dashboard',
      documents: 'Document Management',
      chat: 'AI Assistant',
      analytics: 'Analytics & Insights',
    };
    return map[this.activeView];
  }

  get currentSub(): string {
    const map: Record<View, string> = {
      dashboard: 'Q1 2026 Overview',
      documents: '6 documents uploaded',
      chat: 'Powered by Bedrock + Claude',
      analytics: 'YTD Performance',
    };
    return map[this.activeView];
  }
}
