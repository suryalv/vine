import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'app-analytics',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="analytics">
      <!-- Top Row: Loss Ratio Trend + Risk Distribution -->
      <div class="grid-2">
        <!-- Loss Ratio Trend -->
        <div class="card">
          <div class="card-head">
            <div class="card-title-group">
              <div class="card-icon" style="background: rgba(37,99,235,0.1); color: #2563eb;">
                <lucide-icon name="activity" [size]="16"></lucide-icon>
              </div>
              <h3 class="card-title">Loss Ratio Trend</h3>
            </div>
            <span class="card-subtitle">6-Month Rolling</span>
          </div>
          <div class="bar-chart">
            <div class="bar-group" *ngFor="let d of lossRatioData">
              <div class="bar-wrapper">
                <div class="bar-fill" [style.height]="d.ratio + '%'" [style.background]="d.ratio > 70 ? '#ef4444' : d.ratio > 55 ? '#f59e0b' : '#10b981'">
                  <span class="bar-value">{{ d.ratio }}%</span>
                </div>
              </div>
              <span class="bar-label">{{ d.month }}</span>
            </div>
          </div>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot" style="background: #10b981;"></span> &lt; 55% (Good)</span>
            <span class="legend-item"><span class="legend-dot" style="background: #f59e0b;"></span> 55-70% (Watch)</span>
            <span class="legend-item"><span class="legend-dot" style="background: #ef4444;"></span> &gt; 70% (Poor)</span>
          </div>
        </div>

        <!-- Risk Distribution -->
        <div class="card">
          <div class="card-head">
            <div class="card-title-group">
              <div class="card-icon" style="background: rgba(139,92,246,0.1); color: #8b5cf6;">
                <lucide-icon name="target" [size]="16"></lucide-icon>
              </div>
              <h3 class="card-title">Risk Distribution</h3>
            </div>
            <span class="card-subtitle">Current Portfolio</span>
          </div>
          <div class="donut-container">
            <div class="donut" [style.background]="donutGradient">
              <div class="donut-hole">
                <span class="donut-total">{{ totalPolicies }}</span>
                <span class="donut-total-label">Policies</span>
              </div>
            </div>
            <div class="donut-legend">
              <div class="donut-legend-item" *ngFor="let r of riskDistribution">
                <span class="donut-legend-color" [style.background]="r.color"></span>
                <div class="donut-legend-text">
                  <span class="donut-legend-label">{{ r.label }}</span>
                  <span class="donut-legend-value">{{ r.count }} ({{ r.pct }}%)</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Middle Row: Top Exposures + Claims Frequency -->
      <div class="grid-2">
        <!-- Top Exposures by Region -->
        <div class="card">
          <div class="card-head">
            <div class="card-title-group">
              <div class="card-icon" style="background: rgba(6,182,212,0.1); color: #06b6d4;">
                <lucide-icon name="layers" [size]="16"></lucide-icon>
              </div>
              <h3 class="card-title">Top Exposures by Region</h3>
            </div>
            <span class="card-subtitle">Total Insured Value</span>
          </div>
          <div class="horiz-bars">
            <div class="horiz-row" *ngFor="let e of exposures; let i = index">
              <div class="horiz-rank">{{ i + 1 }}</div>
              <div class="horiz-info">
                <div class="horiz-label-row">
                  <span class="horiz-label">{{ e.region }}</span>
                  <span class="horiz-amount">{{ e.tiv }}</span>
                </div>
                <div class="horiz-track">
                  <div class="horiz-fill" [style.width]="e.pct + '%'" [style.background]="e.color"></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Claims Frequency -->
        <div class="card">
          <div class="card-head">
            <div class="card-title-group">
              <div class="card-icon" style="background: rgba(239,68,68,0.1); color: #ef4444;">
                <lucide-icon name="shield-alert" [size]="16"></lucide-icon>
              </div>
              <h3 class="card-title">Claims Frequency</h3>
            </div>
            <span class="card-subtitle">Quarterly Breakdown</span>
          </div>
          <div class="claims-grid">
            <div class="claims-quarter" *ngFor="let q of claimsFrequency">
              <div class="quarter-header">
                <span class="quarter-label">{{ q.quarter }}</span>
                <span class="quarter-total">{{ q.total }} claims</span>
              </div>
              <div class="sparkline">
                <div class="spark-bar" *ngFor="let v of q.monthly"
                  [style.height]="(v / maxClaimMonthly * 100) + '%'"
                  [style.background]="v > 18 ? '#ef4444' : v > 12 ? '#f59e0b' : 'var(--accent)'">
                </div>
              </div>
              <div class="spark-labels">
                <span *ngFor="let l of q.labels">{{ l }}</span>
              </div>
              <div class="quarter-metrics">
                <div class="qm">
                  <span class="qm-label">Avg Severity</span>
                  <span class="qm-value">{{ q.avgSeverity }}</span>
                </div>
                <div class="qm">
                  <span class="qm-label">Loss Ratio</span>
                  <span class="qm-value" [style.color]="q.lossRatioColor">{{ q.lossRatio }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Bottom Row: Underwriting Performance -->
      <div class="card perf-card">
        <div class="card-head">
          <div class="card-title-group">
            <div class="card-icon" style="background: rgba(16,185,129,0.1); color: #10b981;">
              <lucide-icon name="shield-check" [size]="16"></lucide-icon>
            </div>
            <h3 class="card-title">Underwriting Performance</h3>
          </div>
          <span class="card-subtitle">YTD 2026</span>
        </div>
        <div class="perf-grid">
          <div class="perf-stat" *ngFor="let p of perfMetrics">
            <div class="perf-stat-top">
              <span class="perf-stat-value">{{ p.value }}</span>
              <span class="perf-stat-trend" [class.up]="p.trendUp" [class.down]="!p.trendUp">{{ p.trend }}</span>
            </div>
            <span class="perf-stat-label">{{ p.label }}</span>
            <div class="perf-bar-track">
              <div class="perf-bar-fill" [style.width]="p.barPct + '%'" [style.background]="p.barColor"></div>
            </div>
            <span class="perf-stat-detail">{{ p.detail }}</span>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .analytics { display: flex; flex-direction: column; gap: 1.5rem; }

    .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }

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
    }
    .card-title-group { display: flex; align-items: center; gap: 0.625rem; }
    .card-icon {
      width: 2rem;
      height: 2rem;
      border-radius: 0.5rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .card-title {
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--text-primary);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .card-subtitle {
      font-size: 0.65rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    /* ---- Loss Ratio Bar Chart ---- */
    .bar-chart {
      display: flex;
      align-items: flex-end;
      gap: 1rem;
      height: 12rem;
      padding: 0 0.5rem;
    }
    .bar-group {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      height: 100%;
    }
    .bar-wrapper {
      flex: 1;
      width: 100%;
      display: flex;
      align-items: flex-end;
      justify-content: center;
    }
    .bar-fill {
      width: 100%;
      max-width: 3rem;
      border-radius: 0.375rem 0.375rem 0 0;
      position: relative;
      transition: height 0.8s ease;
      min-height: 1.5rem;
    }
    .bar-value {
      position: absolute;
      top: -1.25rem;
      left: 50%;
      transform: translateX(-50%);
      font-size: 0.65rem;
      font-weight: 700;
      color: var(--text-primary);
      white-space: nowrap;
    }
    .bar-label {
      margin-top: 0.5rem;
      font-size: 0.65rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .chart-legend {
      display: flex;
      justify-content: center;
      gap: 1.25rem;
      margin-top: 1rem;
      padding-top: 0.75rem;
      border-top: 1px solid var(--border);
    }
    .legend-item {
      font-size: 0.625rem;
      font-weight: 600;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      gap: 0.375rem;
    }
    .legend-dot {
      width: 0.5rem;
      height: 0.5rem;
      border-radius: 50%;
      flex-shrink: 0;
    }

    /* ---- Risk Distribution Donut ---- */
    .donut-container {
      display: flex;
      align-items: center;
      gap: 2rem;
      padding: 0.5rem 0;
    }
    .donut {
      width: 10rem;
      height: 10rem;
      border-radius: 50%;
      position: relative;
      flex-shrink: 0;
    }
    .donut-hole {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      width: 6rem;
      height: 6rem;
      border-radius: 50%;
      background: var(--card-bg);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
    }
    .donut-total {
      font-size: 1.5rem;
      font-weight: 800;
      color: var(--text-primary);
      letter-spacing: -0.03em;
    }
    .donut-total-label {
      font-size: 0.6rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .donut-legend { display: flex; flex-direction: column; gap: 0.75rem; flex: 1; }
    .donut-legend-item { display: flex; align-items: center; gap: 0.625rem; }
    .donut-legend-color {
      width: 0.75rem;
      height: 0.75rem;
      border-radius: 0.25rem;
      flex-shrink: 0;
    }
    .donut-legend-text { display: flex; flex-direction: column; }
    .donut-legend-label {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-primary);
    }
    .donut-legend-value {
      font-size: 0.65rem;
      font-weight: 500;
      color: var(--text-muted);
    }

    /* ---- Top Exposures Horizontal Bars ---- */
    .horiz-bars { display: flex; flex-direction: column; gap: 0.875rem; }
    .horiz-row { display: flex; align-items: center; gap: 0.75rem; }
    .horiz-rank {
      width: 1.5rem;
      height: 1.5rem;
      border-radius: 0.375rem;
      background: var(--accent-bg);
      color: var(--accent);
      font-size: 0.65rem;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }
    .horiz-info { flex: 1; }
    .horiz-label-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.375rem;
    }
    .horiz-label {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-primary);
    }
    .horiz-amount {
      font-size: 0.7rem;
      font-weight: 700;
      color: var(--text-secondary);
      font-family: 'SF Mono', monospace;
    }
    .horiz-track {
      height: 0.5rem;
      border-radius: 9999px;
      background: var(--bar-empty);
      overflow: hidden;
    }
    .horiz-fill {
      height: 100%;
      border-radius: 9999px;
      transition: width 0.8s ease;
    }

    /* ---- Claims Frequency ---- */
    .claims-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1rem;
    }
    .claims-quarter {
      padding: 0.75rem;
      border-radius: 0.75rem;
      border: 1px solid var(--border);
      transition: all 0.2s;
    }
    .claims-quarter:hover { border-color: var(--accent-muted); }
    .quarter-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
    }
    .quarter-label {
      font-size: 0.7rem;
      font-weight: 700;
      color: var(--text-primary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .quarter-total {
      font-size: 0.6rem;
      font-weight: 600;
      color: var(--text-muted);
    }
    .sparkline {
      display: flex;
      align-items: flex-end;
      gap: 0.25rem;
      height: 3rem;
    }
    .spark-bar {
      flex: 1;
      border-radius: 0.25rem 0.25rem 0 0;
      min-height: 0.25rem;
      transition: height 0.6s ease;
    }
    .spark-labels {
      display: flex;
      justify-content: space-between;
      margin-top: 0.25rem;
    }
    .spark-labels span {
      font-size: 0.5rem;
      color: var(--text-muted);
      font-weight: 500;
      flex: 1;
      text-align: center;
    }
    .quarter-metrics {
      display: flex;
      gap: 0.75rem;
      margin-top: 0.625rem;
      padding-top: 0.5rem;
      border-top: 1px solid var(--border);
    }
    .qm { display: flex; flex-direction: column; flex: 1; }
    .qm-label {
      font-size: 0.5rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .qm-value {
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-primary);
      margin-top: 0.125rem;
    }

    /* ---- Underwriting Performance ---- */
    .perf-grid {
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 1rem;
    }
    .perf-stat {
      padding: 1rem;
      border-radius: 0.75rem;
      border: 1px solid var(--border);
      transition: all 0.2s;
    }
    .perf-stat:hover { border-color: var(--accent-muted); }
    .perf-stat-top {
      display: flex;
      align-items: baseline;
      gap: 0.5rem;
      margin-bottom: 0.25rem;
    }
    .perf-stat-value {
      font-size: 1.5rem;
      font-weight: 800;
      color: var(--text-primary);
      letter-spacing: -0.03em;
    }
    .perf-stat-trend {
      font-size: 0.65rem;
      font-weight: 700;
    }
    .perf-stat-trend.up { color: #10b981; }
    .perf-stat-trend.down { color: #ef4444; }
    .perf-stat-label {
      font-size: 0.65rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.08em;
      display: block;
      margin-bottom: 0.625rem;
    }
    .perf-bar-track {
      height: 0.375rem;
      border-radius: 9999px;
      background: var(--bar-empty);
      overflow: hidden;
      margin-bottom: 0.5rem;
    }
    .perf-bar-fill {
      height: 100%;
      border-radius: 9999px;
      transition: width 0.8s ease;
    }
    .perf-stat-detail {
      font-size: 0.6rem;
      font-weight: 500;
      color: var(--text-muted);
      line-height: 1.4;
    }

    /* ---- Responsive ---- */
    @media (max-width: 1024px) {
      .grid-2 { grid-template-columns: 1fr; }
      .perf-grid { grid-template-columns: repeat(3, 1fr); }
      .claims-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 640px) {
      .perf-grid { grid-template-columns: repeat(2, 1fr); }
      .claims-grid { grid-template-columns: 1fr; }
      .donut-container { flex-direction: column; align-items: center; }
    }
  `]
})
export class AnalyticsComponent {
  // ---- Loss Ratio Trend ----
  lossRatioData = [
    { month: 'Sep', ratio: 62 },
    { month: 'Oct', ratio: 58 },
    { month: 'Nov', ratio: 71 },
    { month: 'Dec', ratio: 65 },
    { month: 'Jan', ratio: 53 },
    { month: 'Feb', ratio: 48 },
  ];

  // ---- Risk Distribution ----
  riskDistribution = [
    { label: 'Low Risk', count: 124, pct: 38, color: '#10b981' },
    { label: 'Moderate Risk', count: 112, pct: 34, color: '#f59e0b' },
    { label: 'High Risk', count: 58, pct: 18, color: '#ef4444' },
    { label: 'Under Review', count: 32, pct: 10, color: '#8b5cf6' },
  ];

  get totalPolicies(): number {
    return this.riskDistribution.reduce((sum, r) => sum + r.count, 0);
  }

  get donutGradient(): string {
    let accumulated = 0;
    const stops: string[] = [];
    for (const segment of this.riskDistribution) {
      stops.push(`${segment.color} ${accumulated}% ${accumulated + segment.pct}%`);
      accumulated += segment.pct;
    }
    return `conic-gradient(${stops.join(', ')})`;
  }

  // ---- Top Exposures by Region ----
  exposures = [
    { region: 'Southeast (FL, GA, SC)', tiv: '$2.4B', pct: 100, color: '#2563eb' },
    { region: 'Northeast (NY, NJ, CT)', tiv: '$1.8B', pct: 75, color: '#8b5cf6' },
    { region: 'West Coast (CA, OR, WA)', tiv: '$1.5B', pct: 63, color: '#06b6d4' },
    { region: 'Gulf Coast (TX, LA)', tiv: '$1.2B', pct: 50, color: '#f59e0b' },
    { region: 'Midwest (IL, OH, MI)', tiv: '$0.9B', pct: 38, color: '#10b981' },
    { region: 'Mountain West (CO, UT)', tiv: '$0.4B', pct: 17, color: '#64748b' },
  ];

  // ---- Claims Frequency ----
  claimsFrequency = [
    {
      quarter: 'Q1 2025', total: 42,
      monthly: [12, 16, 14], labels: ['Jan', 'Feb', 'Mar'],
      avgSeverity: '$84K', lossRatio: '52%', lossRatioColor: '#10b981'
    },
    {
      quarter: 'Q2 2025', total: 57,
      monthly: [18, 21, 18], labels: ['Apr', 'May', 'Jun'],
      avgSeverity: '$97K', lossRatio: '64%', lossRatioColor: '#f59e0b'
    },
    {
      quarter: 'Q3 2025', total: 68,
      monthly: [22, 24, 22], labels: ['Jul', 'Aug', 'Sep'],
      avgSeverity: '$112K', lossRatio: '73%', lossRatioColor: '#ef4444'
    },
    {
      quarter: 'Q4 2025', total: 39,
      monthly: [15, 13, 11], labels: ['Oct', 'Nov', 'Dec'],
      avgSeverity: '$76K', lossRatio: '47%', lossRatioColor: '#10b981'
    },
  ];

  get maxClaimMonthly(): number {
    let max = 0;
    for (const q of this.claimsFrequency) {
      for (const v of q.monthly) {
        if (v > max) max = v;
      }
    }
    return max;
  }

  // ---- Underwriting Performance ----
  perfMetrics = [
    {
      label: 'Combined Ratio', value: '94.2%', trend: '-3.1%', trendUp: true,
      barPct: 94, barColor: '#10b981',
      detail: 'Target: < 98% | Prior Yr: 97.3%'
    },
    {
      label: 'Written Premium', value: '$48.7M', trend: '+12.4%', trendUp: true,
      barPct: 81, barColor: '#2563eb',
      detail: 'Budget: $60M | 81% attained'
    },
    {
      label: 'Bind Rate', value: '34.8%', trend: '+2.1%', trendUp: true,
      barPct: 70, barColor: '#8b5cf6',
      detail: 'Quoted: 412 | Bound: 143'
    },
    {
      label: 'Avg Premium Size', value: '$342K', trend: '+8.7%', trendUp: true,
      barPct: 68, barColor: '#06b6d4',
      detail: 'Median: $285K | Mode: $200K'
    },
    {
      label: 'Expense Ratio', value: '31.5%', trend: '+0.8%', trendUp: false,
      barPct: 79, barColor: '#f59e0b',
      detail: 'Target: < 30% | Acquisition: 18.2%'
    },
  ];
}
