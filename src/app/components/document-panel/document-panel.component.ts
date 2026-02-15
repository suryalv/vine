import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'app-document-panel',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <section
      class="doc-panel"
      [style.width]="isOpen ? '20rem' : '0'"
      [style.overflow]="isOpen ? 'visible' : 'hidden'"
    >
      <div class="panel-header">
        <h3 class="panel-title">Document Library</h3>
        <button (click)="close.emit()" class="close-btn">
          <lucide-icon name="chevron-right" [size]="16"></lucide-icon>
        </button>
      </div>
      <div class="panel-body custom-scrollbar">
        <!-- Primary document -->
        <div class="doc-item doc-primary">
          <div class="doc-row">
            <div class="doc-icon doc-icon-red">
              <lucide-icon name="file-text" [size]="16"></lucide-icon>
            </div>
            <div>
              <p class="doc-name">Primary_Policy.pdf</p>
              <p class="doc-meta">24 Pages &bull; Scanned</p>
            </div>
          </div>
          <div class="doc-preview">
            <div class="preview-inner">
              <div class="preview-page">
                <div class="line line-title"></div>
                <div class="line line-full"></div>
                <div class="line line-full"></div>
                <div class="line line-half"></div>
                <div class="line-block"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Endorsement doc -->
        <div class="doc-item doc-secondary">
          <div class="doc-row">
            <div class="doc-icon doc-icon-amber">
              <lucide-icon name="file-text" [size]="16"></lucide-icon>
            </div>
            <div>
              <p class="doc-name">Endorsements_v3.pdf</p>
              <p class="doc-meta">8 Pages &bull; Extracted</p>
            </div>
          </div>
        </div>

        <!-- Loss history -->
        <div class="doc-item doc-secondary">
          <div class="doc-row">
            <div class="doc-icon doc-icon-green">
              <lucide-icon name="file-text" [size]="16"></lucide-icon>
            </div>
            <div>
              <p class="doc-name">Loss_History_2023.xlsx</p>
              <p class="doc-meta">3 Sheets &bull; Parsed</p>
            </div>
          </div>
        </div>

        <button class="upload-btn">+ Upload Supplement</button>
      </div>
    </section>
  `,
  styles: [`
    :host { display: block; }
    .doc-panel {
      transition: width 0.5s ease;
      border-right: 1px solid var(--border);
      background: var(--panel-bg);
      display: flex;
      flex-direction: column;
      flex-shrink: 0;
    }
    .panel-header {
      padding: 1.5rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .panel-title {
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.2em;
      color: var(--text-muted);
      text-transform: uppercase;
    }
    .close-btn {
      color: var(--text-muted);
      background: none;
      border: none;
      cursor: pointer;
      transition: color 0.2s;
    }
    .close-btn:hover { color: var(--text-primary); }
    .panel-body {
      flex: 1;
      overflow-y: auto;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }
    .doc-item {
      padding: 1rem;
      border-radius: 0.75rem;
      transition: all 0.3s;
    }
    .doc-primary {
      background: var(--accent-bg);
      border: 1px solid var(--accent-muted);
    }
    .doc-secondary {
      background: var(--impact-bg);
      border: 1px solid var(--border);
      cursor: pointer;
    }
    .doc-secondary:hover { border-color: var(--accent-muted); }
    .doc-row { display: flex; align-items: center; gap: 0.75rem; }
    .doc-icon {
      padding: 0.5rem;
      border-radius: 0.5rem;
    }
    .doc-icon-red { background: rgba(239,68,68,0.15); color: #ef4444; }
    .doc-icon-amber { background: rgba(245,158,11,0.15); color: #f59e0b; }
    .doc-icon-green { background: rgba(16,185,129,0.15); color: #10b981; }
    .doc-name {
      font-size: 0.75rem;
      font-weight: 600;
      color: var(--text-primary);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      max-width: 8rem;
    }
    .doc-meta { font-size: 9px; color: var(--text-muted); }
    .doc-preview {
      height: 8rem;
      width: 100%;
      background: var(--preview-bg);
      border-radius: 0.5rem;
      border: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      margin-top: 0.75rem;
    }
    .preview-inner { transform: scale(0.5); opacity: 0.2; pointer-events: none; }
    .preview-page { width: 16rem; height: 20rem; background: white; padding: 1rem; }
    .line { border-radius: 2px; }
    .line-title { height: 1rem; width: 75%; background: #e2e8f0; margin-bottom: 0.5rem; }
    .line-full { height: 0.5rem; width: 100%; background: #f1f5f9; margin-bottom: 0.25rem; }
    .line-half { height: 0.5rem; width: 66%; background: #f1f5f9; margin-bottom: 1.5rem; }
    .line-block { height: 2.5rem; width: 100%; background: #eef2ff; border-radius: 0.25rem; }
    .upload-btn {
      width: 100%;
      padding: 0.75rem;
      border-radius: 0.75rem;
      border: 1px dashed var(--border);
      font-size: 10px;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.1em;
      background: transparent;
      cursor: pointer;
      transition: all 0.3s;
    }
    .upload-btn:hover {
      border-color: var(--accent-muted);
      color: var(--accent);
    }
  `]
})
export class DocumentPanelComponent {
  @Input() isOpen: boolean = true;
  @Output() close = new EventEmitter<void>();
}
