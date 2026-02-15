import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { ApiService } from '../../services/api.service';

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
            <span class="ws-value" [style.color]="backendUp ? '#10b981' : '#ef4444'">{{ backendUp ? 'Online' : 'Offline' }}</span>
            <span class="ws-label">Backend</span>
          </div>
          <div class="ws-divider"></div>
          <div class="ws">
            <span class="ws-value">{{ geminiReady ? 'Ready' : 'No Key' }}</span>
            <span class="ws-label">Gemini</span>
          </div>
          <div class="ws-divider"></div>
          <div class="ws">
            <span class="ws-value">LanceDB</span>
            <span class="ws-label">Vector Store</span>
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

      <!-- Main Grid -->
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

          <!-- Hallucination Monitor -->
          <div class="card">
            <div class="card-head">
              <div class="card-title-group">
                <div class="card-icon-wrap" style="background: rgba(139,92,246,0.08); color: #8b5cf6;">
                  <lucide-icon name="shield-alert" [size]="15"></lucide-icon>
                </div>
                <h3 class="card-title">Hallucination Monitor</h3>
              </div>
              <span class="card-subtitle">Trust Metrics</span>
            </div>

            <!-- Overall Gauge -->
            <div class="hall-monitor-gauge">
              <svg viewBox="0 0 120 120" class="monitor-svg">
                <circle cx="60" cy="60" r="50" fill="none" stroke="var(--border)" stroke-width="8" />
                <circle cx="60" cy="60" r="50" fill="none" stroke="#10b981" stroke-width="8"
                  stroke-linecap="round"
                  [attr.stroke-dasharray]="(hallAvg * 3.14) + ', 314'"
                  transform="rotate(-90 60 60)"
                  style="transition: stroke-dasharray 1s ease" />
              </svg>
              <div class="monitor-center">
                <span class="monitor-value">{{ hallAvg | number:'1.0-0' }}%</span>
                <span class="monitor-label">Avg Grounding</span>
              </div>
            </div>

            <!-- Factor Breakdown -->
            <div class="hall-factors">
              <div class="hf-row" *ngFor="let f of hallFactors">
                <span class="hf-label">{{ f.label }}</span>
                <div class="hf-bar-track">
                  <div class="hf-bar-fill" [style.width]="f.value + '%'" [style.background]="f.color"></div>
                </div>
                <span class="hf-val">{{ f.value }}%</span>
              </div>
            </div>

            <!-- Recent Ratings -->
            <div class="hall-recent">
              <span class="hall-recent-title">Recent Response Ratings</span>
              <div class="rating-row" *ngFor="let r of recentRatings">
                <div class="rating-dot" [style.background]="r.color"></div>
                <span class="rating-query">{{ r.query }}</span>
                <span class="rating-score" [style.color]="r.color">{{ r.score }}%</span>
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
      display: flex; justify-content: space-between; align-items: center;
      padding: 1.5rem 1.75rem; background: linear-gradient(135deg, var(--accent-bg) 0%, transparent 70%);
      border: 1px solid var(--accent-muted); border-radius: 1rem;
      position: relative; overflow: hidden;
    }
    .welcome-banner::before {
      content: ''; position: absolute; top: -50%; right: -10%;
      width: 20rem; height: 20rem; border-radius: 50%;
      background: var(--accent-muted); opacity: 0.15; filter: blur(60px);
    }
    .welcome-title { font-size: 1.1rem; font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; }
    .welcome-sub { font-size: 0.75rem; color: var(--text-muted); margin-top: 0.375rem; line-height: 1.5; }
    .welcome-sub strong { color: var(--accent); font-weight: 700; }
    .welcome-stats { display: flex; align-items: center; gap: 1.5rem; position: relative; z-index: 1; }
    .ws { display: flex; flex-direction: column; align-items: center; }
    .ws-value { font-size: 1.1rem; font-weight: 800; color: var(--text-primary); letter-spacing: -0.02em; }
    .ws-label {
      font-size: 0.6rem; font-weight: 600; color: var(--text-muted);
      text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.125rem;
    }
    .ws-divider { width: 1px; height: 2rem; background: var(--border); }

    /* ===== Metric Cards ===== */
    .metrics { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; }
    .metric-card {
      background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 1rem;
      padding: 1.25rem; transition: all 0.3s; position: relative; overflow: hidden;
      animation: slideUp 0.4s ease-out both;
    }
    .metric-card:hover { border-color: var(--accent-muted); transform: translateY(-2px); box-shadow: 0 8px 24px var(--card-shadow); }
    .metric-glow {
      position: absolute; top: -1rem; right: -1rem; width: 5rem; height: 5rem;
      border-radius: 50%; opacity: 0.12; filter: blur(20px); pointer-events: none;
    }
    .metric-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; position: relative; }
    .metric-icon { width: 2.5rem; height: 2.5rem; border-radius: 0.75rem; display: flex; align-items: center; justify-content: center; }
    .metric-trend {
      font-size: 0.65rem; font-weight: 700; display: flex; align-items: center; gap: 0.2rem;
      padding: 0.2rem 0.5rem; border-radius: 0.375rem;
    }
    .metric-trend.up { color: #10b981; background: rgba(16,185,129,0.1); }
    .metric-trend.down { color: #ef4444; background: rgba(239,68,68,0.1); }
    .trend-arrow { font-size: 0.5rem; }
    .metric-value { font-size: 1.75rem; font-weight: 800; color: var(--text-primary); letter-spacing: -0.03em; }
    .metric-label {
      font-size: 0.65rem; font-weight: 600; color: var(--text-muted);
      text-transform: uppercase; letter-spacing: 0.1em; margin-top: 0.25rem;
    }
    .metric-sparkline {
      display: flex; align-items: flex-end; gap: 2px; height: 1.5rem;
      margin-top: 0.875rem; padding-top: 0.5rem; border-top: 1px solid var(--border);
    }
    .spark { flex: 1; border-radius: 2px 2px 0 0; opacity: 0.35; min-height: 2px; transition: opacity 0.2s; }
    .metric-card:hover .spark { opacity: 0.6; }

    /* ===== Shared ===== */
    .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 1rem; padding: 1.25rem; }
    .card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 0.75rem; }
    .card-title-group { display: flex; align-items: center; gap: 0.625rem; }
    .card-icon-wrap {
      width: 2rem; height: 2rem; border-radius: 0.5rem; display: flex;
      align-items: center; justify-content: center; flex-shrink: 0;
    }
    .card-title { font-size: 0.8rem; font-weight: 700; color: var(--text-primary); text-transform: uppercase; letter-spacing: 0.08em; }
    .card-subtitle { font-size: 0.6rem; font-weight: 500; color: var(--text-muted); }
    .main-grid { display: grid; grid-template-columns: 1fr 24rem; gap: 1.5rem; }

    /* ===== Filter Buttons ===== */
    .filter-row { display: flex; gap: 0.375rem; }
    .filter-btn {
      padding: 0.35rem 0.7rem; border-radius: 0.5rem; border: 1px solid var(--border);
      background: transparent; color: var(--text-muted); font-size: 0.625rem;
      font-weight: 600; cursor: pointer; transition: all 0.2s;
      text-transform: uppercase; letter-spacing: 0.05em;
    }
    .filter-btn:hover, .filter-btn.active { background: var(--accent-bg); color: var(--accent); border-color: var(--accent-muted); }

    /* ===== Activity Feed ===== */
    .activity-list { display: flex; flex-direction: column; gap: 0.5rem; max-height: 28rem; overflow-y: auto; }
    .activity-item {
      display: flex; align-items: flex-start; gap: 0.75rem; padding: 0.875rem;
      border-radius: 0.75rem; border: 1px solid var(--border); transition: all 0.2s;
      animation: fadeIn 0.3s ease-out both;
    }
    .activity-item:hover { border-color: var(--accent-muted); background: var(--accent-bg); }
    .activity-icon { width: 2.25rem; height: 2.25rem; border-radius: 0.625rem; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
    .activity-body { flex: 1; min-width: 0; }
    .activity-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.375rem; }
    .activity-type-tag {
      font-size: 0.5rem; font-weight: 800; padding: 0.125rem 0.4rem;
      border-radius: 0.25rem; letter-spacing: 0.08em; text-transform: uppercase;
    }
    .activity-time { font-size: 0.575rem; color: var(--text-muted); font-weight: 500; }
    .activity-title { font-size: 0.78rem; font-weight: 600; color: var(--text-primary); line-height: 1.4; }
    .activity-desc { font-size: 0.675rem; color: var(--text-muted); margin-top: 0.25rem; line-height: 1.5; }
    .activity-meta { display: flex; align-items: center; gap: 0.375rem; margin-top: 0.5rem; font-size: 0.6rem; color: var(--text-muted); font-weight: 500; }
    .activity-status { flex-shrink: 0; padding-top: 0.25rem; }
    .status-dot { width: 0.5rem; height: 0.5rem; border-radius: 50%; display: block; }

    /* ===== Right Column ===== */
    .right-col { display: flex; flex-direction: column; gap: 1.5rem; }

    /* ===== Hallucination Monitor ===== */
    .hall-monitor-gauge { position: relative; width: 120px; height: 120px; margin: 0 auto 1rem; }
    .monitor-svg { width: 100%; height: 100%; }
    .monitor-center {
      position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
      display: flex; flex-direction: column; align-items: center;
    }
    .monitor-value { font-size: 1.5rem; font-weight: 800; color: var(--text-primary); letter-spacing: -0.03em; }
    .monitor-label { font-size: 0.55rem; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.08em; }

    .hall-factors { display: flex; flex-direction: column; gap: 0.625rem; margin-bottom: 1rem; }
    .hf-row { display: flex; align-items: center; gap: 0.5rem; }
    .hf-label { font-size: 0.625rem; font-weight: 600; color: var(--text-muted); min-width: 7rem; text-transform: uppercase; letter-spacing: 0.03em; }
    .hf-bar-track { flex: 1; height: 5px; border-radius: 9999px; background: var(--bar-empty); overflow: hidden; }
    .hf-bar-fill { height: 100%; border-radius: 9999px; transition: width 0.8s ease; }
    .hf-val { font-size: 0.625rem; font-weight: 700; color: var(--text-secondary); min-width: 2rem; text-align: right; }

    .hall-recent { border-top: 1px solid var(--border); padding-top: 0.75rem; }
    .hall-recent-title {
      font-size: 0.6rem; font-weight: 700; color: var(--text-muted);
      text-transform: uppercase; letter-spacing: 0.08em; display: block; margin-bottom: 0.625rem;
    }
    .rating-row { display: flex; align-items: center; gap: 0.5rem; padding: 0.375rem 0; }
    .rating-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
    .rating-query {
      flex: 1; font-size: 0.65rem; font-weight: 500; color: var(--text-secondary);
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .rating-score { font-size: 0.65rem; font-weight: 800; min-width: 2rem; text-align: right; }

    /* ===== Quick Actions ===== */
    .quick-actions { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
    .action-btn {
      display: flex; align-items: center; gap: 0.5rem;
      padding: 0.625rem 0.75rem; border-radius: 0.625rem;
      border: 1px solid var(--border); background: transparent;
      color: var(--text-secondary); font-size: 0.675rem; font-weight: 600;
      cursor: pointer; transition: all 0.2s;
    }
    .action-btn:hover { border-color: var(--accent-muted); color: var(--accent); background: var(--accent-bg); }

    @keyframes slideUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

    @media (max-width: 1100px) {
      .main-grid { grid-template-columns: 1fr; }
      .welcome-banner { flex-direction: column; align-items: flex-start; gap: 1rem; }
      .welcome-stats { align-self: stretch; justify-content: space-around; }
    }
    @media (max-width: 768px) { .metrics { grid-template-columns: repeat(2, 1fr); } }
  `]
})
export class DashboardComponent implements OnInit {
  private api = inject(ApiService);

  activityFilter = 'all';
  totalProcessed = 24;
  totalInsights = 67;
  backendUp = false;
  geminiReady = false;

  // Hallucination Monitor data
  hallAvg = 87.2;
  hallFactors = [
    { label: 'Retrieval Conf.', value: 91, color: '#10b981' },
    { label: 'Response Ground.', value: 84, color: '#2563eb' },
    { label: 'Numerical Fidel.', value: 88, color: '#8b5cf6' },
    { label: 'Entity Consist.', value: 86, color: '#06b6d4' },
  ];

  recentRatings = [
    { query: 'What is the TIV for all locations?', score: 94, color: '#10b981' },
    { query: 'List all endorsements', score: 88, color: '#10b981' },
    { query: 'Summarize loss history trends', score: 72, color: '#f59e0b' },
    { query: 'What deductibles apply to FL?', score: 91, color: '#10b981' },
    { query: 'Compare against ISO form', score: 58, color: '#f59e0b' },
  ];

  get greeting(): string {
    const h = new Date().getHours();
    if (h < 12) return 'morning';
    if (h < 17) return 'afternoon';
    return 'evening';
  }

  ngOnInit(): void {
    this.api.healthCheck().subscribe({
      next: (res) => {
        this.backendUp = res.status === 'ok';
        this.geminiReady = res.gemini_configured;
      },
      error: () => {
        this.backendUp = false;
        this.geminiReady = false;
      },
    });
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
      label: 'Avg Grounding Score', value: '87%', icon: 'shield-check',
      iconBg: 'rgba(16,185,129,0.1)', iconColor: '#10b981', glowColor: '#10b981',
      trend: '4%', trendUp: true,
      sparkline: [60, 65, 70, 68, 75, 72, 80, 78, 82, 85, 84, 87]
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
      title: 'Hallucination detected: unverified claim in response',
      desc: 'AI response about deductible amounts could not be traced to source documents. Flagged for manual review.',
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

  quickActions = [
    { icon: 'upload', label: 'Upload Document' },
    { icon: 'sparkles', label: 'Ask AI' },
    { icon: 'activity', label: 'Run Analysis' },
    { icon: 'shield-check', label: 'Risk Review' },
  ];
}
