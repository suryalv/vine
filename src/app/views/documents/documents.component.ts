import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { UWDocument } from '../../models/insight.model';

@Component({
  selector: 'app-documents',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <div class="documents">
      <!-- Upload Drop Zone -->
      <div
        class="upload-zone"
        [class.drag-over]="isDragOver"
        (dragover)="onDragOver($event)"
        (dragleave)="onDragLeave($event)"
        (drop)="onDrop($event)"
        (click)="fileInput.click()"
      >
        <input
          #fileInput
          type="file"
          multiple
          style="display: none"
          (change)="onFileSelect($event)"
        />
        <div class="upload-icon">
          <lucide-icon name="upload" [size]="28"></lucide-icon>
        </div>
        <p class="upload-title">Drop documents here or click to upload</p>
        <p class="upload-hint">Supports PDF, XLSX, DOCX, CSV &mdash; up to 50MB per file</p>
      </div>

      <!-- Section Header -->
      <div class="section-head">
        <h3 class="section-title">Uploaded Documents</h3>
        <span class="doc-count">{{ documents.length }} files</span>
      </div>

      <!-- Documents Grid -->
      <div class="doc-grid">
        <div class="doc-card" *ngFor="let doc of documents">
          <!-- Card Header -->
          <div class="doc-card-head">
            <div class="doc-icon" [style.background]="getTypeColor(doc.type).bg" [style.color]="getTypeColor(doc.type).fg">
              <lucide-icon [name]="getTypeIcon(doc.type)" [size]="18"></lucide-icon>
            </div>
            <span class="status-badge" [ngClass]="'status-' + doc.status">
              {{ statusLabel(doc.status) }}
            </span>
          </div>

          <!-- Doc Info -->
          <p class="doc-name">{{ doc.name }}</p>
          <div class="doc-meta">
            <span class="doc-type">{{ doc.type }}</span>
            <span class="meta-sep">&middot;</span>
            <span class="doc-pages">{{ doc.pages }} pages</span>
          </div>

          <!-- Extraction Progress -->
          <div class="progress-section">
            <div class="progress-head">
              <span class="progress-label">Extraction</span>
              <span class="progress-value">{{ doc.extractedFields }}/{{ doc.totalFields }} fields</span>
            </div>
            <div class="progress-track">
              <div
                class="progress-fill"
                [style.width]="getProgress(doc) + '%'"
                [style.background]="getProgressColor(doc)"
              ></div>
            </div>
          </div>

          <!-- Footer -->
          <div class="doc-footer">
            <span class="doc-date">
              <lucide-icon name="paperclip" [size]="12"></lucide-icon>
              {{ doc.uploadDate }}
            </span>
            <button class="doc-action" (click)="openDocument(doc)">
              <lucide-icon name="arrow-up-right" [size]="14"></lucide-icon>
            </button>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .documents { display: flex; flex-direction: column; gap: 1.5rem; }

    /* Upload Zone */
    .upload-zone {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 0.75rem;
      padding: 2.5rem 2rem;
      border: 2px dashed var(--border);
      border-radius: 1rem;
      background: var(--card-bg);
      cursor: pointer;
      transition: all 0.3s;
    }
    .upload-zone:hover {
      border-color: var(--accent-muted);
      background: var(--accent-bg);
    }
    .upload-zone.drag-over {
      border-color: var(--accent);
      background: var(--accent-bg);
      transform: scale(1.005);
    }
    .upload-icon {
      width: 3.5rem;
      height: 3.5rem;
      border-radius: 1rem;
      display: flex;
      align-items: center;
      justify-content: center;
      background: var(--accent-bg);
      color: var(--accent);
    }
    .upload-title {
      font-size: 0.875rem;
      font-weight: 600;
      color: var(--text-primary);
    }
    .upload-hint {
      font-size: 0.7rem;
      color: var(--text-muted);
    }

    /* Section Header */
    .section-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .section-title {
      font-size: 0.8rem;
      font-weight: 700;
      color: var(--text-primary);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }
    .doc-count {
      font-size: 0.7rem;
      font-weight: 600;
      color: var(--text-muted);
    }

    /* Documents Grid */
    .doc-grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 1rem;
    }

    /* Document Card */
    .doc-card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 1rem;
      padding: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      transition: all 0.3s;
    }
    .doc-card:hover {
      border-color: var(--accent-muted);
    }

    .doc-card-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .doc-icon {
      width: 2.25rem;
      height: 2.25rem;
      border-radius: 0.625rem;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    /* Status Badges */
    .status-badge {
      font-size: 0.6rem;
      font-weight: 700;
      padding: 0.2rem 0.55rem;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .status-uploading {
      background: rgba(139, 92, 246, 0.1);
      color: #8b5cf6;
    }
    .status-processing {
      background: rgba(245, 158, 11, 0.1);
      color: #f59e0b;
    }
    .status-extracted {
      background: rgba(37, 99, 235, 0.1);
      color: #2563eb;
    }
    .status-reviewed {
      background: rgba(16, 185, 129, 0.1);
      color: #10b981;
    }

    /* Doc Info */
    .doc-name {
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-primary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .doc-meta {
      display: flex;
      align-items: center;
      gap: 0.375rem;
      font-size: 0.675rem;
      color: var(--text-muted);
    }
    .doc-type { font-weight: 500; }
    .meta-sep { opacity: 0.5; }
    .doc-pages { font-weight: 500; }

    /* Progress Bar */
    .progress-section {
      display: flex;
      flex-direction: column;
      gap: 0.375rem;
    }
    .progress-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .progress-label {
      font-size: 0.6rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .progress-value {
      font-size: 0.65rem;
      font-weight: 700;
      color: var(--text-secondary);
    }
    .progress-track {
      width: 100%;
      height: 0.375rem;
      border-radius: 9999px;
      background: var(--bar-empty);
      overflow: hidden;
    }
    .progress-fill {
      height: 100%;
      border-radius: 9999px;
      transition: width 0.8s ease;
    }

    /* Footer */
    .doc-footer {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 0.5rem;
      border-top: 1px solid var(--border);
    }
    .doc-date {
      display: flex;
      align-items: center;
      gap: 0.375rem;
      font-size: 0.65rem;
      color: var(--text-muted);
      font-weight: 500;
    }
    .doc-action {
      width: 1.75rem;
      height: 1.75rem;
      border-radius: 0.5rem;
      border: 1px solid var(--border);
      background: transparent;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: all 0.2s;
    }
    .doc-action:hover {
      background: var(--accent-bg);
      color: var(--accent);
      border-color: var(--accent-muted);
    }

    @media (max-width: 1024px) {
      .doc-grid { grid-template-columns: repeat(2, 1fr); }
    }
    @media (max-width: 640px) {
      .doc-grid { grid-template-columns: 1fr; }
    }
  `]
})
export class DocumentsComponent {
  isDragOver = false;

  documents: UWDocument[] = [
    {
      id: 1,
      name: 'Commercial Property Policy — Meridian Steel',
      type: 'Policy PDF',
      pages: 48,
      status: 'reviewed',
      extractedFields: 124,
      totalFields: 124,
      uploadDate: '2024-02-10'
    },
    {
      id: 2,
      name: 'Endorsement Package — Wind & Hail',
      type: 'Endorsement',
      pages: 12,
      status: 'extracted',
      extractedFields: 31,
      totalFields: 38,
      uploadDate: '2024-02-09'
    },
    {
      id: 3,
      name: 'Loss Run Report — 5 Year History',
      type: 'Loss Run',
      pages: 24,
      status: 'processing',
      extractedFields: 42,
      totalFields: 96,
      uploadDate: '2024-02-08'
    },
    {
      id: 4,
      name: 'Statement of Values — All Locations',
      type: 'SOV Spreadsheet',
      pages: 6,
      status: 'extracted',
      extractedFields: 215,
      totalFields: 240,
      uploadDate: '2024-02-07'
    },
    {
      id: 5,
      name: 'ACORD 125 — Commercial Insurance App',
      type: 'Application Form',
      pages: 8,
      status: 'uploading',
      extractedFields: 0,
      totalFields: 64,
      uploadDate: '2024-02-06'
    },
    {
      id: 6,
      name: 'Annual Financial Statements — FY2023',
      type: 'Financial Statement',
      pages: 36,
      status: 'reviewed',
      extractedFields: 78,
      totalFields: 78,
      uploadDate: '2024-02-05'
    }
  ];

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    this.isDragOver = false;
    // File handling would go here
  }

  onFileSelect(event: Event): void {
    // File handling would go here
  }

  openDocument(doc: UWDocument): void {
    // Navigation logic would go here
  }

  getProgress(doc: UWDocument): number {
    if (doc.totalFields === 0) return 0;
    return Math.round((doc.extractedFields / doc.totalFields) * 100);
  }

  getProgressColor(doc: UWDocument): string {
    const pct = this.getProgress(doc);
    if (pct === 100) return '#10b981';
    if (pct >= 60) return '#2563eb';
    if (pct >= 30) return '#f59e0b';
    return '#8b5cf6';
  }

  statusLabel(status: string): string {
    const map: Record<string, string> = {
      uploading: 'Uploading',
      processing: 'Processing',
      extracted: 'Extracted',
      reviewed: 'Reviewed'
    };
    return map[status] || status;
  }

  getTypeIcon(type: string): string {
    const map: Record<string, string> = {
      'Policy PDF': 'shield-check',
      'Endorsement': 'layers',
      'Loss Run': 'activity',
      'SOV Spreadsheet': 'target',
      'Application Form': 'file-text',
      'Financial Statement': 'sparkles'
    };
    return map[type] || 'file-text';
  }

  getTypeColor(type: string): { bg: string; fg: string } {
    const map: Record<string, { bg: string; fg: string }> = {
      'Policy PDF': { bg: 'rgba(37,99,235,0.1)', fg: '#2563eb' },
      'Endorsement': { bg: 'rgba(139,92,246,0.1)', fg: '#8b5cf6' },
      'Loss Run': { bg: 'rgba(239,68,68,0.1)', fg: '#ef4444' },
      'SOV Spreadsheet': { bg: 'rgba(6,182,212,0.1)', fg: '#06b6d4' },
      'Application Form': { bg: 'rgba(245,158,11,0.1)', fg: '#f59e0b' },
      'Financial Statement': { bg: 'rgba(16,185,129,0.1)', fg: '#10b981' }
    };
    return map[type] || { bg: 'rgba(100,116,139,0.1)', fg: '#64748b' };
  }
}
