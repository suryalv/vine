import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { Insight } from '../../models/insight.model';

@Component({
  selector: 'app-insight-card',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div
      class="insight-card animate-float-in"
      [style.animation-delay]="animationDelay"
    >
      <!-- Header -->
      <div class="card-header">
        <div class="header-left">
          <div
            class="icon-badge"
            [ngClass]="{
              'badge-critical': insight.type === 'critical',
              'badge-warning': insight.type === 'warning',
              'badge-info': insight.type === 'info'
            }"
          >
            <lucide-icon
              [name]="insight.type === 'critical' ? 'shield-alert' : 'shield-check'"
              [size]="20"
            ></lucide-icon>
          </div>
          <div>
            <p class="category-label">{{ insight.category }}</p>
            <h3 class="card-title">{{ insight.title }}</h3>
          </div>
        </div>
        <div class="confidence">
          <span class="confidence-label">{{ insight.confidence }}% MATCH</span>
          <div class="confidence-bars">
            <div
              *ngFor="let bar of confidenceBars; let i = index"
              class="bar"
              [class.filled]="i < filledBars"
            ></div>
          </div>
        </div>
      </div>

      <!-- Content -->
      <p class="card-content">{{ insight.content }}</p>

      <!-- Footer -->
      <div class="card-footer">
        <div class="impact-box">
          <span class="impact-label">Predicted Impact</span>
          <span
            class="impact-value"
            [ngClass]="{
              'text-critical': insight.type === 'critical',
              'text-warning': insight.type === 'warning',
              'text-info': insight.type === 'info'
            }"
          >
            {{ insight.impact }}
          </span>
        </div>
        <button class="pdf-btn">
          <lucide-icon name="target" [size]="14"></lucide-icon>
          Open Context in PDF
          <lucide-icon name="arrow-up-right" [size]="12"></lucide-icon>
        </button>
      </div>
    </div>
  `,
  styles: [`
    :host { display: block; }
    .insight-card {
      position: relative;
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 1.5rem;
      padding: 2rem;
      transition: all 0.5s ease;
      opacity: 0;
    }
    .insight-card:hover {
      border-color: var(--accent-muted);
      box-shadow: 0 8px 32px var(--card-shadow);
    }
    .card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      margin-bottom: 1.5rem;
    }
    .header-left { display: flex; align-items: center; gap: 0.75rem; }
    .icon-badge {
      padding: 0.625rem;
      border-radius: 0.75rem;
    }
    .badge-critical { background: rgba(239,68,68,0.1); color: #ef4444; }
    .badge-warning { background: rgba(249,115,22,0.1); color: #f97316; }
    .badge-info { background: var(--accent-bg); color: var(--accent); }
    .category-label {
      font-size: 9px;
      font-weight: 700;
      letter-spacing: 0.2em;
      color: var(--text-muted);
      text-transform: uppercase;
    }
    .card-title {
      font-size: 1.125rem;
      font-weight: 700;
      color: var(--text-primary);
      transition: color 0.3s;
    }
    .insight-card:hover .card-title { color: var(--accent); }
    .confidence { display: flex; flex-direction: column; align-items: flex-end; }
    .confidence-label {
      font-size: 0.75rem;
      font-family: 'SF Mono', 'Fira Code', monospace;
      color: var(--text-muted);
    }
    .confidence-bars { display: flex; gap: 2px; margin-top: 4px; }
    .bar {
      width: 4px;
      height: 12px;
      border-radius: 9999px;
      background: var(--bar-empty);
      transition: background 0.5s;
    }
    .bar.filled { background: var(--accent); }
    .card-content {
      color: var(--text-secondary);
      line-height: 1.7;
      margin-bottom: 1.5rem;
      font-size: 0.875rem;
    }
    .card-footer {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 1rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border);
    }
    .impact-box {
      background: var(--impact-bg);
      border-radius: 0.75rem;
      padding: 0.75rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .impact-label {
      font-size: 10px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }
    .impact-value { font-size: 0.75rem; font-weight: 700; }
    .text-critical { color: #ef4444; }
    .text-warning { color: #f97316; }
    .text-info { color: var(--text-secondary); }
    .pdf-btn {
      background: var(--accent-bg);
      color: var(--accent);
      border-radius: 0.75rem;
      padding: 0 1rem;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 0.5rem;
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      border: none;
      cursor: pointer;
      transition: all 0.3s;
    }
    .pdf-btn:hover { background: var(--accent-hover-bg); }
  `]
})
export class InsightCardComponent {
  @Input() insight!: Insight;
  @Input() index: number = 0;

  confidenceBars = [1, 2, 3, 4, 5];

  get filledBars(): number {
    return Math.round(this.insight.confidence / 20);
  }

  get animationDelay(): string {
    return `${this.index * 0.15}s`;
  }
}
