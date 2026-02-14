import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="dash">

      <!-- Welcome Banner -->
      <div class="welcome-banner">
        <div class="welcome-left">
          <h2 class="welcome-title">Good {{ greeting }}, Underwriter</h2>
          <p class="welcome-sub">Your AI companion has processed <strong>{{ totalProcessed }}</strong> documents and generated <strong>{{ totalInsights }}</strong> insights today.</p>
        </div>
        <div class="welcome-stats">
          <div class="ws">
            <span class="ws-value">98.4%</span>
            <span class="ws-label">AI Accuracy</span>
          </div>
          <div class="ws-divider"></div>
          <div class="ws">
            <span class="ws-value">2.3s</span>
            <span class="ws-label">Avg Response</span>
          </div>
          <div class="ws-divider"></div>
          <div class="ws">
            <span class="ws-value">14hr</span>
            <span class="ws-label">Time Saved</span>
          </div>
        </div>
      </div>

      <!-- Metrics Row -->
      <div class="metrics">
        <div class="metric-card" *ngFor="let m of metrics; let i = index" [style.animation-delay]="(i * 80) + 'ms'">
          <div class="metric-glow" [style.background]="m.glowColor"></div>
          <div class="metric-top">
            <div class="metric-icon" [style.background]="m.iconBg" [style.color]="m.iconColor">
              <lucide-icon [name]="m.icon" [size]="18"></lucide-icon>
            </div>
            <span class="metric-trend" [class.up]="m.trendUp" [class.down]="!m.trendUp">
              <span class="trend-arrow">{{ m.trendUp ? '&#9650;' : '&#9660;' }}</span>
              {{ m.trend }}
            </span>
          </div>
          <p class="metric-value">{{ m.value }}</p>
          <p class="metric-label">{{ m.label }}</p>
          <div class="metric-sparkline">
            <div class="spark" *ngFor="let h of m.sparkline" [style.height]="h + '%'" [style.background]="m.iconColor"></div>
          </div>
        </div>
      </div>

      <!-- Main Grid: Activity + Right Column -->
      <div class="main-grid">

        <!-- AI Activity Feed -->
        <div class="card">
          <div class="card-head">
            <div class="card-title-group">
              <div class="card-icon-wrap" style="background: rgba(37,99,235,0.08); color: #2563eb;">
                <lucide-icon name="sparkles" [size]="15"></lucide-icon>
              </div>
              <div>
                <h3 class="card-title">AI Activity Feed</h3>
                <span class="card-subtitle">Recent companion actions</span>
              </div>
            </div>
            <div class="filter-row">
              <button *ngFor="let f of activityFilters" class="filter-btn" [class.active]="activityFilter === f.key" (click)="activityFilter = f.key">
                {{ f.label }}
              </button>
            </div>
          </div>

          <div class="activity-list custom-scrollbar">
            <div class="activity-item" *ngFor="let a of filteredActivities; let i = index" [style.animation-delay]="(i * 50) + 'ms'">
              <div class="activity-icon" [style.background]="a.iconBg" [style.color]="a.iconColor">
                <lucide-icon [name]="a.icon" [size]="15"></lucide-icon>
              </div>
              <div class="activity-body">
                <div class="activity-header">
                  <span class="activity-type-tag" [style.background]="a.tagBg" [style.color]="a.tagColor">{{ a.type }}</span>
                  <span class="activity-time">{{ a.time }}</span>
                </div>
                <p class="activity-title">{{ a.title }}</p>
                <p class="activity-desc">{{ a.desc }}</p>
                <div class="activity-meta" *ngIf="a.document">
                  <lucide-icon name="file-text" [size]="11"></lucide-icon>
                  <span>{{ a.document }}</span>
                </div>
              </div>
              <div class="activity-status">
                <span class="status-dot" [style.background]="a.statusColor"></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column -->
        <div class="right-col">

          <!-- AI Insights Summary -->
          <div class="card">
            <div class="card-head">
              <div class="card-title-group">
                <div class="card-icon-wrap" style="background: rgba(139,92,246,0.08); color: #8b5cf6;">
                  <lucide-icon name="zap" [size]="15"></lucide-icon>
                </div>
                <h3 class="card-title">Insights Summary</h3>
              </div>
              <span class="card-subtitle">Today</span>
            </div>
            <div class="insights-grid">
              <div class="insight-item" *ngFor="let ins of insightsSummary">
                <div class="insight-count" [style.color]="ins.color">{{ ins.count }}</div>
                <div class="insight-info">
                  <span class="insight-label">{{ ins.label }}</span>
                  <div class="insight-bar-track">
                    <div class="insight-bar-fill" [style.width]="ins.pct + '%'" [style.background]="ins.color"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Document Processing Queue -->
          <div class="card">
            <div class="card-head">
              <div class="card-title-group">
                <div class="card-icon-wrap" style="background: rgba(6,182,212,0.08); color: #06b6d4;">
                  <lucide-icon name="layers" [size]="15"></lucide-icon>
                </div>
                <h3 class="card-title">Processing Queue</h3>
              </div>
              <span class="queue-count-badge">{{ processingQueue.length }}</span>
            </div>
            <div class="queue-list">
              <div class="queue-item" *ngFor="let q of processingQueue">
                <div class="queue-icon" [style.background]="q.iconBg" [style.color]="q.iconColor">
                  <lucide-icon name="file-text" [size]="14"></lucide-icon>
                </div>
                <div class="queue-body">
                  <span class="queue-name">{{ q.name }}</span>
                  <div class="queue-progress-track">
                    <div class="queue-progress-fill" [style.width]="q.progress + '%'" [style.background]="q.progressColor"></div>
                  </div>
                </div>
                <span class="queue-pct">{{ q.progress }}%</span>
              </div>
            </div>
          </div>

          <!-- Quick Actions -->
          <div class="card">
            <div class="card-head">
              <div class="card-title-group">
                <div class="card-icon-wrap" style="background: rgba(16,185,129,0.08); color: #10b981;">
                  <lucide-icon name="sparkles" [size]="15"></lucide-icon>
                </div>
                <h3 class="card-title">Quick Actions</h3>
              </div>
            </div>
            <div class="quick-actions">
              <button class="action-btn" *ngFor="let act of quickActions">
                <lucide-icon [name]="act.icon" [size]="16"></lucide-icon>
                <span>{{ act.label }}</span>
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  `,
  styles: [`
    .dash { display: flex; flex-direction: column; gap: 1.5rem; }

    /* ===== Welcome Banner ===== */
    .welcome-banner {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 1.5rem 1.75rem;
      background: linear-gradient(135deg, var(--accent-bg) 0%, transparent 70%);
      border: 1px solid var(--accent-muted);
      border-radius: 1rem;
      position: relative;
      overflow: hidden;
    }
    .welcome-banner::before {
      content: '';
      position: absolute;
      top: -50%;
      right: -10%;
      width: 20rem;
      height: 20rem;
      border-radius: 50%;
      background: var(--accent-muted);
      opacity: 0.15;
      filter: blur(60px);
    }
    .welcome-title {
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--text-primary);
      letter-spacing: -0.01em;
    }
    .welcome-sub {
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 0.375rem;
      line-height: 1.5;
    }
    .welcome-sub strong {
      color: var(--accent);
      font-weight: 700;
    }
    .welcome-stats {
      display: flex;
      align-items: center;
      gap: 1.5rem;
      position: relative;
      z-index: 1;
    }
    .ws { display: flex; flex-direction: column; align-items: center; }
    .ws-value {
      font-size: 1.1rem;
      font-weight: 800;
      color: var(--text-primary);
      letter-spacing: -0.02em;
    }
    .ws-label {
      font-size: 0.6rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-top: 0.125rem;
    }
    .ws-divider {
      width: 1px;
      height: 2rem;
      background: var(--border);
    }

    /* ===== Metric Cards ===== */
    .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
    .metric-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 1rem;
      padding: 1.25rem;
      transition: all 0.3s;
      position: relative;
      overflow: hidden;
      animation: slideUp 0.4s ease-out both;
    }
    .metric-card:hover {
      border-color: var(--accent-muted);
      transform: translateY(-2px);
      box-shadow: 0 8px 24px var(--card-shadow);
    }
    .metric-glow {
      position: absolute;
      top: -1rem;
      right: -1rem;
      width: 5rem;
      height: 5rem;
      border-radius: 50%;
      opacity: 0.12;
      filter: blur(20px);
      pointer-events: none;
    }
    .metric-top {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1rem;
      position: relative;
    }
    .metric-icon {
      width: 2.5rem;
      height: 2.5rem;
      border-radius: 0.75rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .metric-trend {
      font-size: 0.65rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      gap: 0.2rem;
      padding: 0.2rem 0.5rem;
      border-radius: 0.375rem;
    }
    .metric-trend.up { color: #10b981; background: rgba(16,185,129,0.1); }
    .metric-trend.down { color: #ef4444; background: rgba(239,68,68,0.1); }
    .trend-arrow { font-size: 0.5rem; }
    .metric-value {
      font-size: 1.75rem;
      font-weight: 800;
      color: var(--text-primary);
      letter-spacing: -0.03em;
    }
    .metric-label {
      font-size: 0.65rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      margin-top: 0.25rem;
    }
    .metric-sparkline {
      display: flex;
      align-items: flex-end;
      gap: 2px;
      height: 1.5rem;
      margin-top: 0.875rem;
      padding-top: 0.5rem;
      border-top: 1px solid var(--border);
    }
    .spark {
      flex: 1;
      border-radius: 2px 2px 0 0;
      opacity: 0.35;
      min-height: 2px;
      transition: opacity 0.2s;
    }
    .metric-card:hover .spark { opacity: 0.6; }

    /* ===== Shared ===== */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 1rem;
      padding: 1.25rem;
    }
    .card-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
      flex-wrap: wrap;
      gap: 0.75rem;
    }
    .card-title-group { display: flex; align-items: center; gap: 0.625rem; }
    .card-icon-wrap {
      width: 2rem;
      height: 2rem;
      border-radius: 0.5rem;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .card-title {
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--text-primary);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .card-subtitle {
      font-size: 0.6rem;
      font-weight: 500;
      color: var(--text-muted);
    }
    .main-grid { display: grid; grid-template-columns: 1fr 24rem; gap: 1.5rem; }

    /* ===== Filter Buttons ===== */
    .filter-row { display: flex; gap: 0.375rem; }
    .filter-btn {
      padding: 0.35rem 0.7rem;
      border-radius: 0.5rem;
      border: 1px solid var(--border);
      background: transparent;
      color: var(--text-muted);
      font-size: 0.625rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .filter-btn:hover, .filter-btn.active {
      background: var(--accent-bg);
      color: var(--accent);
      border-color: var(--accent-muted);
    }

    /* ===== AI Activity Feed ===== */
    .activity-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      max-height: 28rem;
      overflow-y: auto;
    }
    .activity-item {
      display: flex;
      align-items: flex-start;
      gap: 0.75rem;
      padding: 0.875rem;
      border-radius: 0.75rem;
      border: 1px solid var(--border);
      transition: all 0.2s;
      animation: fadeIn 0.3s ease-out both;
    }
    .activity-item:hover {
      border-color: var(--accent-muted);
      background: var(--accent-bg);
    }
    .activity-icon {
      width: 2.25rem;
      height: 2.25rem;
      border-radius: 0.625rem;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .activity-body { flex: 1; min-width: 0; }
    .activity-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.375rem;
    }
    .activity-type-tag {
      font-size: 0.5rem;
      font-weight: 800;
      padding: 0.125rem 0.4rem;
      border-radius: 0.25rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    .activity-time {
      font-size: 0.575rem;
      color: var(--text-muted);
      font-weight: 500;
    }
    .activity-title {
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-primary);
      line-height: 1.4;
    }
    .activity-desc {
      font-size: 0.675rem;
      color: var(--text-muted);
      margin-top: 0.25rem;
      line-height: 1.5;
    }
    .activity-meta {
      display: flex;
      align-items: center;
      gap: 0.375rem;
      margin-top: 0.5rem;
      font-size: 0.6rem;
      color: var(--text-muted);
      font-weight: 500;
    }
    .activity-status { flex-shrink: 0; padding-top: 0.25rem; }
    .status-dot {
      width: 0.5rem;
      height: 0.5rem;
      border-radius: 50%;
      display: block;
    }

    /* ===== Right Column ===== */
    .right-col { display: flex; flex-direction: column; gap: 1.5rem; }

    /* ===== Insights Summary ===== */
    .insights-grid { display: flex; flex-direction: column; gap: 1rem; }
    .insight-item { display: flex; align-items: center; gap: 0.75rem; }
    .insight-count {
      font-size: 1.25rem;
      font-weight: 800;
      min-width: 2.25rem;
      text-align: center;
      letter-spacing: -0.02em;
    }
    .insight-info { flex: 1; }
    .insight-label {
      font-size: 0.7rem;
      font-weight: 600;
      color: var(--text-primary);
      display: block;
      margin-bottom: 0.375rem;
    }
    .insight-bar-track {
      height: 0.375rem;
      border-radius: 9999px;
      background: var(--bar-empty);
      overflow: hidden;
    }
    .insight-bar-fill {
      height: 100%;
      border-radius: 9999px;
      transition: width 0.8s ease;
    }

    /* ===== Processing Queue ===== */
    .queue-count-badge {
      font-size: 0.6rem;
      font-weight: 800;
      width: 1.375rem;
      height: 1.375rem;
      border-radius: 50%;
      background: rgba(6,182,212,0.12);
      color: #06b6d4;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .queue-list { display: flex; flex-direction: column; gap: 0.625rem; }
    .queue-item {
      display: flex;
      align-items: center;
      gap: 0.625rem;
      padding: 0.625rem;
      border-radius: 0.625rem;
      border: 1px solid var(--border);
      transition: all 0.2s;
    }
    .queue-item:hover { border-color: var(--accent-muted); }
    .queue-icon {
      width: 1.75rem;
      height: 1.75rem;
      border-radius: 0.5rem;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .queue-body { flex: 1; min-width: 0; }
    .queue-name {
      font-size: 0.7rem;
      font-weight: 600;
      color: var(--text-primary);
      display: block;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      margin-bottom: 0.375rem;
    }
    .queue-progress-track {
      height: 0.3rem;
      border-radius: 9999px;
      background: var(--bar-empty);
      overflow: hidden;
    }
    .queue-progress-fill {
      height: 100%;
      border-radius: 9999px;
      transition: width 0.8s ease;
    }
    .queue-pct {
      font-size: 0.65rem;
      font-weight: 700;
      color: var(--text-secondary);
      min-width: 2rem;
      text-align: right;
    }

    /* ===== Quick Actions ===== */
    .quick-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 0.5rem;
    }
    .action-btn {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.625rem 0.75rem;
      border-radius: 0.625rem;
      border: 1px solid var(--border);
      background: transparent;
      color: var(--text-secondary);
      font-size: 0.675rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }
    .action-btn:hover {
      border-color: var(--accent-muted);
      color: var(--accent);
      background: var(--accent-bg);
    }

    /* ===== Animations ===== */
    @keyframes slideUp {
      from { opacity: 0; transform: translateY(12px); }
      to { opacity: 1; transform: translateY(0); }
    }
    @keyframes fadeIn {
      from { opacity: 0; }
      to { opacity: 1; }
    }

    /* ===== Responsive ===== */
    @media (max-width: 1100px) {
      .main-grid { grid-template-columns: 1fr; }
      .welcome-banner { flex-direction: column; align-items: flex-start; gap: 1rem; }
      .welcome-stats { align-self: stretch; justify-content: space-around; }
    }
    @media (max-width: 768px) {
      .metrics { grid-template-columns: repeat(2, 1fr); }
    }
  `]
})
export class DashboardComponent {
  activityFilter = 'all';
  totalProcessed = 24;
  totalInsights = 67;

  get greeting(): string {
    const h = new Date().getHours();
    if (h < 12) return 'morning';
    if (h < 17) return 'afternoon';
    return 'evening';
  }

  metrics = [
    {
      label: 'Documents Analyzed', value: '24', icon: 'file-text',
      iconBg: 'rgba(37,99,235,0.1)', iconColor: '#2563eb', glowColor: '#2563eb',
      trend: '18%', trendUp: true,
      sparkline: [30, 45, 38, 62, 55, 70, 65, 80, 72, 85, 78, 90]
    },
    {
      label: 'AI Insights Generated', value: '67', icon: 'sparkles',
      iconBg: 'rgba(139,92,246,0.1)', iconColor: '#8b5cf6', glowColor: '#8b5cf6',
      trend: '24%', trendUp: true,
      sparkline: [20, 35, 40, 38, 55, 50, 65, 60, 75, 70, 82, 88]
    },
    {
      label: 'Risk Flags Detected', value: '12', icon: 'shield-alert',
      iconBg: 'rgba(239,68,68,0.1)', iconColor: '#ef4444', glowColor: '#ef4444',
      trend: '3', trendUp: false,
      sparkline: [75, 72, 78, 80, 76, 74, 79, 73, 71, 75, 72, 70]
    },
    {
      label: 'Fields Extracted', value: '1,842', icon: 'target',
      iconBg: 'rgba(16,185,129,0.1)', iconColor: '#10b981', glowColor: '#10b981',
      trend: '96%', trendUp: true,
      sparkline: [22, 28, 25, 30, 27, 32, 29, 35, 33, 38, 34, 40]
    },
  ];

  activityFilters = [
    { key: 'all', label: 'All' },
    { key: 'extraction', label: 'Extraction' },
    { key: 'analysis', label: 'Analysis' },
    { key: 'risk', label: 'Risk' },
  ];

  activities = [
    {
      type: 'EXTRACTION', category: 'extraction',
      icon: 'file-text', iconBg: 'rgba(37,99,235,0.1)', iconColor: '#2563eb',
      tagBg: 'rgba(37,99,235,0.1)', tagColor: '#2563eb',
      title: 'Extracted 124 fields from Commercial Property Policy',
      desc: 'Named insured, policy limits, deductibles, coverage forms, and endorsement schedules successfully parsed.',
      document: 'Meridian_Steel_CPP_2026.pdf',
      time: '3m ago', statusColor: '#10b981'
    },
    {
      type: 'RISK FLAG', category: 'risk',
      icon: 'shield-alert', iconBg: 'rgba(239,68,68,0.1)', iconColor: '#ef4444',
      tagBg: 'rgba(239,68,68,0.1)', tagColor: '#ef4444',
      title: 'High aggregate exposure detected in FL wind zone',
      desc: 'Current CAT model shows PML at 92% of treaty capacity. Recommend reviewing facultative placement.',
      document: 'SOV_All_Locations_Q1.xlsx',
      time: '8m ago', statusColor: '#ef4444'
    },
    {
      type: 'ANALYSIS', category: 'analysis',
      icon: 'sparkles', iconBg: 'rgba(139,92,246,0.1)', iconColor: '#8b5cf6',
      tagBg: 'rgba(139,92,246,0.1)', tagColor: '#8b5cf6',
      title: 'Loss ratio trend analysis complete for Acme Manufacturing',
      desc: 'Combined ratio improved from 97.3% to 94.2% YoY. Products liability severity declining 12% per annum.',
      document: 'Acme_Loss_Runs_5yr.pdf',
      time: '15m ago', statusColor: '#10b981'
    },
    {
      type: 'EXTRACTION', category: 'extraction',
      icon: 'file-text', iconBg: 'rgba(37,99,235,0.1)', iconColor: '#2563eb',
      tagBg: 'rgba(37,99,235,0.1)', tagColor: '#2563eb',
      title: 'ACORD 125 application form digitized',
      desc: 'All 64 fields extracted with 99.1% confidence. 3 fields flagged for manual verification.',
      document: 'ACORD_125_Pacific_Coast.pdf',
      time: '22m ago', statusColor: '#f59e0b'
    },
    {
      type: 'ANALYSIS', category: 'analysis',
      icon: 'sparkles', iconBg: 'rgba(139,92,246,0.1)', iconColor: '#8b5cf6',
      tagBg: 'rgba(139,92,246,0.1)', tagColor: '#8b5cf6',
      title: 'Endorsement comparison report generated',
      desc: 'Compared manuscript endorsements against ISO CG 00 01 (04/13). Found 4 broadening provisions exceeding market standard.',
      document: 'Endorsement_WindHail_2026.pdf',
      time: '35m ago', statusColor: '#10b981'
    },
    {
      type: 'RISK FLAG', category: 'risk',
      icon: 'shield-alert', iconBg: 'rgba(239,68,68,0.1)', iconColor: '#ef4444',
      tagBg: 'rgba(239,68,68,0.1)', tagColor: '#ef4444',
      title: 'Contractual liability gap identified',
      desc: 'Downstream distribution agreements lack proper indemnification clauses. Recommend CG 24 04 endorsement.',
      document: null,
      time: '48m ago', statusColor: '#f59e0b'
    },
    {
      type: 'EXTRACTION', category: 'extraction',
      icon: 'file-text', iconBg: 'rgba(37,99,235,0.1)', iconColor: '#2563eb',
      tagBg: 'rgba(37,99,235,0.1)', tagColor: '#2563eb',
      title: 'Financial statement analysis completed',
      desc: 'Revenue: $142M, Net Income: $8.7M, Debt-to-Equity: 0.84. Financial health rated as Strong.',
      document: 'Northwind_FY2025_Financials.pdf',
      time: '1h ago', statusColor: '#10b981'
    },
  ];

  get filteredActivities() {
    if (this.activityFilter === 'all') return this.activities;
    return this.activities.filter(a => a.category === this.activityFilter);
  }

  insightsSummary = [
    { label: 'Coverage Gaps Found', count: 8, pct: 75, color: '#ef4444' },
    { label: 'Rate Recommendations', count: 15, pct: 60, color: '#2563eb' },
    { label: 'Endorsement Suggestions', count: 22, pct: 88, color: '#8b5cf6' },
    { label: 'Compliance Checks Passed', count: 22, pct: 92, color: '#10b981' },
  ];

  processingQueue = [
    { name: 'GL_Policy_TechVault_2026.pdf', progress: 78, progressColor: '#2563eb', iconBg: 'rgba(37,99,235,0.08)', iconColor: '#2563eb' },
    { name: 'SOV_Harbor_Point_Marina.xlsx', progress: 45, progressColor: '#f59e0b', iconBg: 'rgba(245,158,11,0.08)', iconColor: '#f59e0b' },
    { name: 'ACORD_140_Marine_Cargo.pdf', progress: 12, progressColor: '#8b5cf6', iconBg: 'rgba(139,92,246,0.08)', iconColor: '#8b5cf6' },
  ];

  quickActions = [
    { icon: 'upload', label: 'Upload Document' },
    { icon: 'sparkles', label: 'Ask AI' },
    { icon: 'activity', label: 'Run Analysis' },
    { icon: 'shield-check', label: 'Risk Review' },
  ];
}
