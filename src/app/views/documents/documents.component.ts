import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { UWDocument } from '../../models/insight.model';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-documents',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  template: `
    <div class="documents">
      <!-- Upload Drop Zone -->
      <div
        class="upload-zone"
        [class.drag-over]="isDragOver"
        [class.uploading]="isUploading"
        (dragover)="onDragOver($event)"
        (dragleave)="onDragLeave($event)"
        (drop)="onDrop($event)"
        (click)="fileInput.click()"
      >
        <input
          #fileInput
          type="file"
          multiple
          accept=".pdf,.docx,.doc"
          style="display: none"
          (change)="onFileSelect($event)"
        />
        <div class="upload-icon" *ngIf="!isUploading">
          <lucide-icon name="upload" [size]="28"></lucide-icon>
        </div>
        <div class="upload-spinner" *ngIf="isUploading">
          <lucide-icon name="refresh-cw" [size]="28" class="spin-icon"></lucide-icon>
        </div>
        <p class="upload-title">{{ isUploading ? 'Processing & indexing document...' : 'Drop documents here or click to upload' }}</p>
        <p class="upload-hint" *ngIf="!isUploading">Supports PDF, DOCX &mdash; files are chunked & embedded automatically</p>
        <p class="upload-hint" *ngIf="isUploading">{{ uploadStatus }}</p>
      </div>

      <!-- Error / Success messages -->
      <div *ngIf="uploadMessage" class="upload-message" [class.success]="!uploadError" [class.error]="uploadError">
        <lucide-icon [name]="uploadError ? 'alert-triangle' : 'check-circle'" [size]="14"></lucide-icon>
        <span>{{ uploadMessage }}</span>
        <button class="dismiss-btn" (click)="uploadMessage = ''">
          <lucide-icon name="x" [size]="12"></lucide-icon>
        </button>
      </div>

      <!-- Section Header -->
      <div class="section-head">
        <h3 class="section-title">Uploaded Documents</h3>
        <span class="doc-count">{{ filteredDocuments.length }} of {{ documents.length }} files</span>
      </div>

      <!-- Admin Bar -->
      <div class="admin-bar" *ngIf="documents.length > 0">
        <label class="select-all" (click)="$event.stopPropagation()">
          <input type="checkbox" [checked]="allSelected" (change)="toggleSelectAll()" />
          <span>Select All</span>
        </label>
        <div class="admin-controls">
          <div class="filter-wrap">
            <lucide-icon name="search" [size]="13" class="filter-icon"></lucide-icon>
            <input class="filter-input" placeholder="Filter by name..." [(ngModel)]="filterText" />
          </div>
          <select class="sort-select" [(ngModel)]="sortBy" (ngModelChange)="applySort()">
            <option value="date">Sort: Date</option>
            <option value="name">Sort: Name</option>
            <option value="chunks">Sort: Chunks</option>
          </select>
          <button *ngIf="selectedDocIds.size > 0" class="bulk-delete-btn" (click)="bulkDelete()">
            <lucide-icon name="trash-2" [size]="13"></lucide-icon>
            Delete Selected ({{ selectedDocIds.size }})
          </button>
        </div>
      </div>

      <!-- Documents Grid -->
      <div class="doc-grid">
        <div class="doc-card" *ngFor="let doc of filteredDocuments"
             [class.selected]="doc.documentId && selectedDocIds.has(doc.documentId)">
          <div class="doc-card-head">
            <div class="card-left">
              <input *ngIf="doc.documentId" type="checkbox"
                     class="doc-checkbox"
                     [checked]="selectedDocIds.has(doc.documentId)"
                     (change)="toggleSelect(doc)"
                     (click)="$event.stopPropagation()" />
              <div class="doc-icon" [style.background]="getTypeColor(doc.type).bg" [style.color]="getTypeColor(doc.type).fg">
                <lucide-icon [name]="getTypeIcon(doc.type)" [size]="18"></lucide-icon>
              </div>
            </div>
            <span class="status-badge" [ngClass]="'status-' + doc.status">
              {{ statusLabel(doc.status) }}
            </span>
          </div>
          <p class="doc-name">{{ doc.name }}</p>
          <div class="doc-meta">
            <span class="doc-type">{{ doc.type }}</span>
            <span class="meta-sep">&middot;</span>
            <span class="doc-pages">{{ doc.pages }} pages</span>
            <span *ngIf="doc.numChunks" class="meta-sep">&middot;</span>
            <span *ngIf="doc.numChunks" class="doc-chunks">{{ doc.numChunks }} chunks</span>
          </div>
          <div class="progress-section">
            <div class="progress-head">
              <span class="progress-label">{{ doc.status === 'indexed' ? 'Indexed' : 'Extraction' }}</span>
              <span class="progress-value">{{ doc.status === 'indexed' ? '100%' : doc.extractedFields + '/' + doc.totalFields + ' fields' }}</span>
            </div>
            <div class="progress-track">
              <div class="progress-fill"
                [style.width]="getProgress(doc) + '%'"
                [style.background]="getProgressColor(doc)"></div>
            </div>
          </div>
          <div class="doc-footer">
            <span class="doc-date">
              <lucide-icon name="paperclip" [size]="12"></lucide-icon>
              {{ doc.uploadDate }}
            </span>
            <div class="doc-actions">
              <button *ngIf="doc.documentId" class="doc-action delete" (click)="deleteDocument(doc)" title="Remove from vector store">
                <lucide-icon name="trash-2" [size]="13"></lucide-icon>
              </button>
              <button class="doc-action" (click)="openDocument(doc)">
                <lucide-icon name="arrow-up-right" [size]="14"></lucide-icon>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .documents { display: flex; flex-direction: column; gap: 1.5rem; }

    /* Upload Zone */
    .upload-zone {
      display: flex; flex-direction: column; align-items: center; justify-content: center;
      gap: 0.75rem; padding: 2.5rem 2rem; border: 2px dashed var(--border);
      border-radius: 1rem; background: var(--card-bg); cursor: pointer; transition: all 0.3s;
    }
    .upload-zone:hover { border-color: var(--accent-muted); background: var(--accent-bg); }
    .upload-zone.drag-over { border-color: var(--accent); background: var(--accent-bg); transform: scale(1.005); }
    .upload-zone.uploading { border-color: var(--accent); border-style: solid; cursor: wait; }
    .upload-icon {
      width: 3.5rem; height: 3.5rem; border-radius: 1rem; display: flex;
      align-items: center; justify-content: center; background: var(--accent-bg); color: var(--accent);
    }
    .upload-spinner {
      width: 3.5rem; height: 3.5rem; border-radius: 1rem; display: flex;
      align-items: center; justify-content: center; background: var(--accent-bg); color: var(--accent);
    }
    .spin-icon { animation: spin 1.2s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .upload-title { font-size: 0.875rem; font-weight: 600; color: var(--text-primary); }
    .upload-hint { font-size: 0.7rem; color: var(--text-muted); }

    /* Messages */
    .upload-message {
      display: flex; align-items: center; gap: 8px; padding: 10px 14px;
      border-radius: 8px; font-size: 0.75rem; font-weight: 600;
      animation: fadeIn 0.3s ease;
    }
    .upload-message.success { background: rgba(16,185,129,0.08); color: #10b981; border: 1px solid rgba(16,185,129,0.2); }
    .upload-message.error { background: rgba(239,68,68,0.08); color: #ef4444; border: 1px solid rgba(239,68,68,0.2); }
    .dismiss-btn {
      margin-left: auto; background: none; border: none; cursor: pointer;
      color: inherit; opacity: 0.6; padding: 2px;
    }
    .dismiss-btn:hover { opacity: 1; }

    /* Section Header */
    .section-head { display: flex; justify-content: space-between; align-items: center; }
    .section-title {
      font-size: 0.8rem; font-weight: 700; color: var(--text-primary);
      text-transform: uppercase; letter-spacing: 0.08em;
    }
    .doc-count { font-size: 0.7rem; font-weight: 600; color: var(--text-muted); }

    /* Admin Bar */
    .admin-bar {
      display: flex; align-items: center; justify-content: space-between;
      padding: 0.625rem 1rem; border-radius: 0.75rem;
      background: var(--card-bg); border: 1px solid var(--card-border);
    }
    .select-all {
      display: flex; align-items: center; gap: 0.5rem;
      font-size: 0.7rem; font-weight: 600; color: var(--text-secondary);
      cursor: pointer;
    }
    .select-all input[type="checkbox"] {
      width: 14px; height: 14px; accent-color: var(--accent); cursor: pointer;
    }
    .admin-controls { display: flex; align-items: center; gap: 0.75rem; }
    .filter-wrap {
      display: flex; align-items: center; gap: 0.375rem;
      padding: 0.3rem 0.625rem; border-radius: 0.5rem;
      background: var(--bg); border: 1px solid var(--border);
    }
    .filter-icon { color: var(--text-muted); }
    .filter-input {
      background: transparent; border: none; outline: none;
      font-size: 0.7rem; color: var(--text-primary); width: 120px;
    }
    .filter-input::placeholder { color: var(--text-muted); }
    .sort-select {
      padding: 0.3rem 0.5rem; border-radius: 0.5rem;
      background: var(--bg); border: 1px solid var(--border);
      font-size: 0.7rem; color: var(--text-primary); cursor: pointer; outline: none;
    }
    .bulk-delete-btn {
      display: flex; align-items: center; gap: 0.375rem;
      padding: 0.35rem 0.75rem; border-radius: 0.5rem;
      background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.3);
      color: #ef4444; font-size: 0.7rem; font-weight: 600;
      cursor: pointer; transition: all 0.2s;
    }
    .bulk-delete-btn:hover { background: rgba(239,68,68,0.15); }

    /* Grid */
    .doc-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
    .doc-card {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-radius: 1rem; padding: 1.25rem; display: flex;
      flex-direction: column; gap: 0.75rem; transition: all 0.3s;
    }
    .doc-card:hover { border-color: var(--accent-muted); }
    .doc-card.selected { border-color: var(--accent); background: var(--accent-bg); }
    .doc-card-head { display: flex; justify-content: space-between; align-items: center; }
    .card-left { display: flex; align-items: center; gap: 0.5rem; }
    .doc-checkbox {
      width: 14px; height: 14px; accent-color: var(--accent); cursor: pointer;
    }
    .doc-icon {
      width: 2.25rem; height: 2.25rem; border-radius: 0.625rem;
      display: flex; align-items: center; justify-content: center;
    }

    .status-badge {
      font-size: 0.6rem; font-weight: 700; padding: 0.2rem 0.55rem;
      border-radius: 9999px; text-transform: uppercase; letter-spacing: 0.05em;
    }
    .status-uploading { background: rgba(139,92,246,0.1); color: #8b5cf6; }
    .status-processing { background: rgba(245,158,11,0.1); color: #f59e0b; }
    .status-extracted { background: rgba(37,99,235,0.1); color: #2563eb; }
    .status-reviewed { background: rgba(16,185,129,0.1); color: #10b981; }
    .status-indexed { background: rgba(6,182,212,0.1); color: #06b6d4; }

    .doc-name {
      font-size: 0.8rem; font-weight: 600; color: var(--text-primary);
      white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    }
    .doc-meta {
      display: flex; align-items: center; gap: 0.375rem;
      font-size: 0.675rem; color: var(--text-muted);
    }
    .doc-type { font-weight: 500; }
    .meta-sep { opacity: 0.5; }
    .doc-pages, .doc-chunks { font-weight: 500; }

    .progress-section { display: flex; flex-direction: column; gap: 0.375rem; }
    .progress-head { display: flex; justify-content: space-between; align-items: center; }
    .progress-label {
      font-size: 0.6rem; font-weight: 600; color: var(--text-muted);
      text-transform: uppercase; letter-spacing: 0.05em;
    }
    .progress-value { font-size: 0.65rem; font-weight: 700; color: var(--text-secondary); }
    .progress-track {
      width: 100%; height: 0.375rem; border-radius: 9999px;
      background: var(--bar-empty); overflow: hidden;
    }
    .progress-fill { height: 100%; border-radius: 9999px; transition: width 0.8s ease; }

    .doc-footer {
      display: flex; justify-content: space-between; align-items: center;
      padding-top: 0.5rem; border-top: 1px solid var(--border);
    }
    .doc-date {
      display: flex; align-items: center; gap: 0.375rem;
      font-size: 0.65rem; color: var(--text-muted); font-weight: 500;
    }
    .doc-actions { display: flex; gap: 4px; }
    .doc-action {
      width: 1.75rem; height: 1.75rem; border-radius: 0.5rem;
      border: 1px solid var(--border); background: transparent;
      color: var(--text-muted); display: flex; align-items: center;
      justify-content: center; cursor: pointer; transition: all 0.2s;
    }
    .doc-action:hover { background: var(--accent-bg); color: var(--accent); border-color: var(--accent-muted); }
    .doc-action.delete:hover { background: rgba(239,68,68,0.08); color: #ef4444; border-color: rgba(239,68,68,0.3); }

    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @media (max-width: 1024px) { .doc-grid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 640px) { .doc-grid { grid-template-columns: 1fr; } }
  `]
})
export class DocumentsComponent {
  private api = inject(ApiService);

  isDragOver = false;
  isUploading = false;
  uploadMessage = '';
  uploadError = false;
  uploadStatus = '';

  documents: UWDocument[] = [];
  selectedDocIds = new Set<string>();
  filterText = '';
  sortBy = 'date';

  private nextId = 1;

  constructor() {
    this.loadDocuments();
  }

  get filteredDocuments(): UWDocument[] {
    let docs = this.documents;
    if (this.filterText) {
      const q = this.filterText.toLowerCase();
      docs = docs.filter(d => d.name.toLowerCase().includes(q));
    }
    return docs;
  }

  get allSelected(): boolean {
    const filtered = this.filteredDocuments.filter(d => !!d.documentId);
    return filtered.length > 0 && filtered.every(d => this.selectedDocIds.has(d.documentId!));
  }

  toggleSelect(doc: UWDocument): void {
    if (!doc.documentId) return;
    if (this.selectedDocIds.has(doc.documentId)) {
      this.selectedDocIds.delete(doc.documentId);
    } else {
      this.selectedDocIds.add(doc.documentId);
    }
  }

  toggleSelectAll(): void {
    if (this.allSelected) {
      this.selectedDocIds.clear();
    } else {
      for (const doc of this.filteredDocuments) {
        if (doc.documentId) this.selectedDocIds.add(doc.documentId);
      }
    }
  }

  bulkDelete(): void {
    const ids = Array.from(this.selectedDocIds);
    this.api.bulkDeleteDocuments(ids).subscribe({
      next: () => {
        this.documents = this.documents.filter(
          d => !d.documentId || !this.selectedDocIds.has(d.documentId)
        );
        this.uploadMessage = `${ids.length} document${ids.length > 1 ? 's' : ''} removed`;
        this.uploadError = false;
        this.selectedDocIds.clear();
      },
      error: () => {
        this.uploadMessage = 'Bulk delete failed';
        this.uploadError = true;
      },
    });
  }

  applySort(): void {
    const key = this.sortBy;
    this.documents.sort((a, b) => {
      if (key === 'name') return a.name.localeCompare(b.name);
      if (key === 'chunks') return (b.numChunks || 0) - (a.numChunks || 0);
      return (b.uploadDate || '').localeCompare(a.uploadDate || '');
    });
  }

  private loadDocuments(): void {
    this.api.listDocuments().subscribe({
      next: (docs) => {
        this.documents = docs.map((d, i) => {
          const ext = d.filename.split('.').pop()?.toLowerCase() || '';
          const docType = ext === 'pdf' ? 'Policy PDF' : 'DOCX Document';
          return {
            id: this.nextId++,
            name: d.filename.replace(/\.[^.]+$/, '').replace(/_/g, ' '),
            type: docType,
            pages: d.num_pages,
            status: 'indexed' as const,
            extractedFields: d.num_chunks,
            totalFields: d.num_chunks,
            uploadDate: d.upload_time ? d.upload_time.split('T')[0] : new Date().toISOString().split('T')[0],
            documentId: d.document_id,
            numChunks: d.num_chunks,
          };
        });
      },
      error: () => {},
    });
  }

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
    const files = event.dataTransfer?.files;
    if (files) {
      for (let i = 0; i < files.length; i++) {
        this.uploadFile(files[i]);
      }
    }
  }

  onFileSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      for (let i = 0; i < input.files.length; i++) {
        this.uploadFile(input.files[i]);
      }
      input.value = '';
    }
  }

  private uploadFile(file: File): void {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !['pdf', 'docx', 'doc'].includes(ext)) {
      this.uploadMessage = `Unsupported file type: .${ext}. Use PDF or DOCX.`;
      this.uploadError = true;
      return;
    }

    this.isUploading = true;
    this.uploadMessage = '';
    this.uploadStatus = `Parsing & embedding ${file.name}...`;

    this.api.uploadDocument(file).subscribe({
      next: (res) => {
        this.isUploading = false;
        this.uploadMessage = `${res.filename} indexed — ${res.num_chunks} chunks from ${res.num_pages} pages`;
        this.uploadError = false;

        const docType = ext === 'pdf' ? 'Policy PDF' : 'DOCX Document';
        this.documents.unshift({
          id: this.nextId++,
          name: res.filename.replace(/\.[^.]+$/, '').replace(/_/g, ' '),
          type: docType,
          pages: res.num_pages,
          status: 'indexed',
          extractedFields: res.num_chunks,
          totalFields: res.num_chunks,
          uploadDate: new Date().toISOString().split('T')[0],
          documentId: res.document_id,
          numChunks: res.num_chunks,
        });
      },
      error: (err) => {
        this.isUploading = false;
        this.uploadMessage = err.error?.detail || err.message || 'Upload failed';
        this.uploadError = true;
      },
    });
  }

  deleteDocument(doc: UWDocument): void {
    if (!doc.documentId) return;
    this.api.deleteDocument(doc.documentId).subscribe({
      next: () => {
        this.documents = this.documents.filter(d => d.id !== doc.id);
        this.uploadMessage = `${doc.name} removed from vector store`;
        this.uploadError = false;
      },
      error: () => {
        this.uploadMessage = 'Failed to delete document';
        this.uploadError = true;
      },
    });
  }

  openDocument(doc: UWDocument): void {}

  getProgress(doc: UWDocument): number {
    if (doc.status === 'indexed') return 100;
    if (doc.totalFields === 0) return 0;
    return Math.round((doc.extractedFields / doc.totalFields) * 100);
  }

  getProgressColor(doc: UWDocument): string {
    if (doc.status === 'indexed') return '#06b6d4';
    const pct = this.getProgress(doc);
    if (pct === 100) return '#10b981';
    if (pct >= 60) return '#2563eb';
    if (pct >= 30) return '#f59e0b';
    return '#8b5cf6';
  }

  statusLabel(status: string): string {
    const map: Record<string, string> = {
      uploading: 'Uploading', processing: 'Processing',
      extracted: 'Extracted', reviewed: 'Reviewed', indexed: 'Indexed',
    };
    return map[status] || status;
  }

  getTypeIcon(type: string): string {
    const map: Record<string, string> = {
      'Policy PDF': 'shield-check', 'Endorsement': 'layers',
      'Loss Run': 'activity', 'SOV Spreadsheet': 'target',
      'Application Form': 'file-text', 'Financial Statement': 'sparkles',
      'DOCX Document': 'file-text',
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
      'Financial Statement': { bg: 'rgba(16,185,129,0.1)', fg: '#10b981' },
      'DOCX Document': { bg: 'rgba(37,99,235,0.1)', fg: '#2563eb' },
    };
    return map[type] || { bg: 'rgba(100,116,139,0.1)', fg: '#64748b' };
  }
}
