import { Component, ElementRef, ViewChild, AfterViewChecked, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { ChatMessage, HallucinationReport, UWAction } from '../../models/insight.model';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule, LucideAngularModule],
  template: `
    <div class="chat-container">
      <!-- Header -->
      <div class="chat-header">
        <div class="header-left">
          <lucide-icon name="sparkles" [size]="18" class="header-icon"></lucide-icon>
          <span class="header-title">UW Companion AI</span>
          <span class="connection-badge" [class.connected]="backendConnected" [class.disconnected]="!backendConnected">
            {{ backendConnected ? 'Connected' : 'Offline' }}
          </span>
        </div>
        <span class="header-subtitle">RAG + Hallucination Detection</span>
      </div>

      <!-- Message Feed -->
      <div class="chat-feed" #chatFeed (scroll)="onChatFeedScroll()">
        <!-- Hallucination Alert Banner -->
        <div *ngIf="showHallucinationBanner" class="hallucination-banner"
             [class.banner-high]="hallucinationBannerRating === 'high'"
             [class.banner-medium]="hallucinationBannerRating === 'medium'">
          <div class="banner-content">
            <lucide-icon name="alert-triangle" [size]="16" class="banner-icon"></lucide-icon>
            <div class="banner-text">
              <span class="banner-title" *ngIf="hallucinationBannerRating === 'high'">Low confidence response</span>
              <span class="banner-title" *ngIf="hallucinationBannerRating === 'medium'">Partially supported response</span>
              <span class="banner-desc" *ngIf="hallucinationBannerRating === 'high'">
                This answer has limited support from your documents (score: {{ hallucinationBannerScore | number:'1.0-0' }}%). Verify key claims independently.
              </span>
              <span class="banner-desc" *ngIf="hallucinationBannerRating === 'medium'">
                Some claims may go beyond what your documents state (score: {{ hallucinationBannerScore | number:'1.0-0' }}%). Expand the grounding panel for details.
              </span>
            </div>
          </div>
          <button class="banner-dismiss" (click)="dismissHallucinationBanner()">
            <lucide-icon name="x" [size]="14"></lucide-icon>
          </button>
        </div>

        <div
          *ngFor="let msg of messages"
          class="message-row"
          [class.user-row]="msg.role === 'user'"
          [class.ai-row]="msg.role === 'ai'"
        >
          <div class="message-bubble" [class.user-bubble]="msg.role === 'user'" [class.ai-bubble]="msg.role === 'ai'">
            <div *ngIf="msg.role === 'ai'" class="ai-indicator">
              <lucide-icon name="zap" [size]="14" class="ai-indicator-icon"></lucide-icon>
              <span class="ai-label">AI Assistant</span>
            </div>
            <p class="message-content">{{ msg.content }}</p>
            <span class="message-time">{{ msg.timestamp }}</span>

            <!-- Hallucination Meter (AI messages only) -->
            <div *ngIf="msg.role === 'ai' && msg.hallucination" class="hallucination-panel">
              <div class="hall-header" (click)="msg._expanded = !msg._expanded">
                <div class="hall-score-wrap">
                  <div class="hall-gauge">
                    <svg viewBox="0 0 36 36" class="gauge-svg">
                      <path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                      <path class="gauge-fill" [attr.stroke]="getHallColor(msg.hallucination)"
                        [attr.stroke-dasharray]="msg.hallucination.overall_score + ', 100'"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" />
                    </svg>
                    <span class="gauge-text">{{ msg.hallucination.overall_score | number:'1.0-0' }}</span>
                  </div>
                  <div class="hall-summary">
                    <span class="hall-badge" [style.background]="getHallBadgeBg(msg.hallucination)" [style.color]="getHallColor(msg.hallucination)">
                      {{ getHallLabel(msg.hallucination) }}
                    </span>
                    <span class="hall-subtitle">Grounding Score</span>
                    <span class="hall-explanation">{{ getHallLabelExplanation(msg.hallucination) }}</span>
                  </div>
                </div>
                <lucide-icon [name]="msg._expanded ? 'chevron-right' : 'chevron-right'" [size]="14" class="hall-expand"
                  [style.transform]="msg._expanded ? 'rotate(90deg)' : 'rotate(0)'"></lucide-icon>
              </div>

              <!-- Expanded Details -->
              <div *ngIf="msg._expanded" class="hall-details">
                <!-- Factor Bars -->
                <div class="factor-grid">
                  <div class="factor-row-group" *ngFor="let factor of [
                    { key: 'retrieval_confidence', value: msg.hallucination.retrieval_confidence },
                    { key: 'response_grounding', value: msg.hallucination.response_grounding },
                    { key: 'numerical_fidelity', value: msg.hallucination.numerical_fidelity },
                    { key: 'entity_consistency', value: msg.hallucination.entity_consistency }
                  ]">
                    <div class="factor-row">
                      <span class="factor-label">{{ getFactorDisplayLabel(factor.key) }}</span>
                      <div class="factor-bar-track">
                        <div class="factor-bar-fill" [style.width]="factor.value + '%'"
                          [style.background]="getFactorColor(factor.value)"></div>
                      </div>
                      <span class="factor-val">{{ factor.value | number:'1.0-0' }}%</span>
                    </div>
                    <p class="factor-explanation">{{ getFactorExplanation(factor.key, factor.value) }}</p>
                  </div>
                </div>

                <!-- Flagged Claims -->
                <div *ngIf="msg.hallucination.flagged_claims.length > 0" class="flagged-section">
                  <div class="flagged-header">
                    <lucide-icon name="alert-triangle" [size]="12"></lucide-icon>
                    <span>Claims not fully supported by your documents</span>
                  </div>
                  <div class="flagged-item" *ngFor="let claim of msg.hallucination.flagged_claims">
                    {{ claim }}
                  </div>
                </div>

                <!-- Source References -->
                <div *ngIf="msg.sources && msg.sources.length > 0" class="sources-section">
                  <div class="sources-header">
                    <lucide-icon name="file-text" [size]="12"></lucide-icon>
                    <span>Source References</span>
                  </div>
                  <div class="source-item" *ngFor="let src of msg.sources; let i = index">
                    <span class="source-num">{{ i + 1 }}</span>
                    <div class="source-body">
                      <span class="source-file">{{ src.source }} · p{{ src.page }}</span>
                      <span class="source-sim">{{ (src.similarity * 100) | number:'1.0-0' }}% match</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- UW Actions (AI messages only) -->
            <div *ngIf="msg.role === 'ai' && msg.actions && msg.actions.length > 0" class="actions-panel">
              <div class="actions-header">
                <lucide-icon name="zap" [size]="12"></lucide-icon>
                <span>Recommended Actions</span>
              </div>
              <div class="action-item" *ngFor="let act of msg.actions">
                <span class="action-priority" [class]="'priority-' + act.priority">{{ act.priority }}</span>
                <div class="action-body">
                  <span class="action-title">{{ act.action }}</span>
                  <span class="action-category">{{ formatCategory(act.category) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Typing indicator -->
        <div *ngIf="isTyping" class="message-row ai-row">
          <div class="message-bubble ai-bubble">
            <div class="ai-indicator">
              <lucide-icon name="zap" [size]="14" class="ai-indicator-icon"></lucide-icon>
              <span class="ai-label">AI Assistant</span>
            </div>
            <div class="typing-indicator">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </div>
      </div>

      <!-- Suggestion Chips -->
      <div class="suggestions-bar">
        <button
          *ngFor="let chip of suggestionChips"
          class="suggestion-chip"
          (click)="sendSuggestion(chip)"
        >
          <lucide-icon name="sparkles" [size]="12" class="chip-icon"></lucide-icon>
          {{ chip }}
        </button>
      </div>

      <!-- Input Bar -->
      <div class="input-bar">
        <input
          #fileInput
          type="file"
          multiple
          accept=".pdf,.docx,.doc"
          style="display: none"
          (change)="onFileSelect($event)"
        />
        <button class="attach-btn" title="Upload document" (click)="fileInput.click()" [disabled]="isUploading">
          <lucide-icon [name]="isUploading ? 'refresh-cw' : 'paperclip'" [size]="18" [class.spin-icon]="isUploading"></lucide-icon>
        </button>
        <input
          type="text"
          class="chat-input"
          placeholder="Ask about your uploaded documents..."
          [(ngModel)]="newMessage"
          (keydown.enter)="sendMessage()"
        />
        <button
          class="send-btn"
          [class.active]="newMessage.trim().length > 0"
          (click)="sendMessage()"
          [disabled]="newMessage.trim().length === 0 || isTyping"
        >
          <lucide-icon name="send" [size]="18"></lucide-icon>
        </button>
      </div>
    </div>
  `,
  styles: `
    :host { display: block; height: 100%; }
    .chat-container {
      display: flex; flex-direction: column; height: 100%;
      background: var(--bg); border: 1px solid var(--card-border);
      border-radius: 12px; overflow: hidden;
    }

    /* Header */
    .chat-header {
      display: flex; align-items: center; justify-content: space-between;
      padding: 14px 20px; background: var(--card-bg); border-bottom: 1px solid var(--border);
    }
    .header-left { display: flex; align-items: center; gap: 8px; }
    .header-icon { color: var(--accent); }
    .header-title { font-size: 15px; font-weight: 600; color: var(--text-primary); }
    .header-subtitle { font-size: 12px; color: var(--text-muted); }
    .connection-badge {
      font-size: 9px; font-weight: 700; padding: 2px 8px; border-radius: 9999px;
      text-transform: uppercase; letter-spacing: 0.05em;
    }
    .connection-badge.connected { background: rgba(16,185,129,0.1); color: #10b981; }
    .connection-badge.disconnected { background: rgba(239,68,68,0.1); color: #ef4444; }

    /* Feed */
    .chat-feed {
      flex: 1; overflow-y: auto; padding: 20px;
      display: flex; flex-direction: column; gap: 16px;
    }
    .chat-feed::-webkit-scrollbar { width: 6px; }
    .chat-feed::-webkit-scrollbar-track { background: transparent; }
    .chat-feed::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

    .message-row { display: flex; width: 100%; }
    .ai-row { justify-content: flex-start; }
    .user-row { justify-content: flex-end; }
    .message-bubble { max-width: 80%; padding: 12px 16px; border-radius: 12px; position: relative; }
    .ai-bubble {
      background: var(--card-bg); border: 1px solid var(--card-border);
      border-left: 3px solid var(--accent); border-radius: 4px 12px 12px 4px;
    }
    .user-bubble { background: var(--accent-bg); border: 1px solid var(--accent-muted); color: var(--text-primary); }
    .ai-indicator { display: flex; align-items: center; gap: 6px; margin-bottom: 8px; }
    .ai-indicator-icon { color: var(--accent); }
    .ai-label {
      font-size: 11px; font-weight: 600; color: var(--accent);
      text-transform: uppercase; letter-spacing: 0.5px;
    }
    .message-content {
      font-size: 14px; line-height: 1.6; color: var(--text-primary);
      margin: 0; white-space: pre-wrap;
    }
    .message-time { display: block; font-size: 11px; color: var(--text-muted); margin-top: 8px; }

    /* Typing */
    .typing-indicator { display: flex; gap: 4px; padding: 4px 0; }
    .dot {
      width: 7px; height: 7px; border-radius: 50%; background: var(--text-muted);
      animation: typingBounce 1.4s infinite ease-in-out;
    }
    .dot:nth-child(2) { animation-delay: 0.2s; }
    .dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typingBounce {
      0%, 80%, 100% { opacity: 0.3; transform: scale(0.8); }
      40% { opacity: 1; transform: scale(1); }
    }

    /* ======= Hallucination Panel ======= */
    .hallucination-panel {
      margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--border);
    }
    .hall-header {
      display: flex; align-items: center; justify-content: space-between;
      cursor: pointer; padding: 4px 0;
    }
    .hall-score-wrap { display: flex; align-items: center; gap: 10px; }
    .hall-gauge { position: relative; width: 36px; height: 36px; }
    .gauge-svg { width: 100%; height: 100%; transform: rotate(-90deg); }
    .gauge-bg {
      fill: none; stroke: var(--border); stroke-width: 3;
      stroke-dasharray: 100, 100;
    }
    .gauge-fill {
      fill: none; stroke-width: 3; stroke-linecap: round;
      transition: stroke-dasharray 0.8s ease;
    }
    .gauge-text {
      position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
      font-size: 9px; font-weight: 800; color: var(--text-primary);
    }
    .hall-summary { display: flex; flex-direction: column; gap: 2px; }
    .hall-badge {
      font-size: 9px; font-weight: 800; padding: 1px 6px; border-radius: 4px;
      text-transform: uppercase; letter-spacing: 0.05em; display: inline-block; width: fit-content;
    }
    .hall-subtitle { font-size: 10px; color: var(--text-muted); font-weight: 500; }
    .hall-expand { color: var(--text-muted); transition: transform 0.2s; }

    /* Expanded Details */
    .hall-details {
      margin-top: 12px; display: flex; flex-direction: column; gap: 12px;
      animation: fadeIn 0.2s ease;
    }
    .factor-grid { display: flex; flex-direction: column; gap: 8px; }
    .factor-row { display: flex; align-items: center; gap: 8px; }
    .factor-label {
      font-size: 10px; font-weight: 600; color: var(--text-muted);
      min-width: 120px; text-transform: uppercase; letter-spacing: 0.03em;
    }
    .factor-bar-track {
      flex: 1; height: 5px; border-radius: 9999px;
      background: var(--bar-empty); overflow: hidden;
    }
    .factor-bar-fill {
      height: 100%; border-radius: 9999px; transition: width 0.8s ease;
    }
    .factor-val {
      font-size: 10px; font-weight: 700; color: var(--text-secondary);
      min-width: 32px; text-align: right;
    }

    /* Flagged Claims */
    .flagged-section {
      padding: 8px 10px; border-radius: 8px;
      background: rgba(239,68,68,0.05); border: 1px solid rgba(239,68,68,0.15);
    }
    .flagged-header {
      display: flex; align-items: center; gap: 6px; color: #ef4444;
      font-size: 10px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.05em; margin-bottom: 6px;
    }
    .flagged-item {
      font-size: 11px; color: var(--text-secondary); line-height: 1.5;
      padding: 4px 0; border-bottom: 1px solid rgba(239,68,68,0.08);
    }
    .flagged-item:last-child { border-bottom: none; }

    /* Source References */
    .sources-section {
      padding: 8px 10px; border-radius: 8px;
      background: rgba(37,99,235,0.05); border: 1px solid rgba(37,99,235,0.12);
    }
    .sources-header {
      display: flex; align-items: center; gap: 6px; color: #2563eb;
      font-size: 10px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.05em; margin-bottom: 6px;
    }
    .source-item {
      display: flex; align-items: center; gap: 8px;
      padding: 4px 0; border-bottom: 1px solid rgba(37,99,235,0.06);
    }
    .source-item:last-child { border-bottom: none; }
    .source-num {
      width: 18px; height: 18px; border-radius: 50%;
      background: rgba(37,99,235,0.1); color: #2563eb;
      font-size: 9px; font-weight: 800;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }
    .source-body { display: flex; flex-direction: column; }
    .source-file { font-size: 11px; font-weight: 600; color: var(--text-primary); }
    .source-sim { font-size: 10px; color: var(--text-muted); }

    /* ======= Actions Panel ======= */
    .actions-panel {
      margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border);
    }
    .actions-header {
      display: flex; align-items: center; gap: 6px; color: var(--accent);
      font-size: 10px; font-weight: 700; text-transform: uppercase;
      letter-spacing: 0.05em; margin-bottom: 8px;
    }
    .action-item {
      display: flex; align-items: flex-start; gap: 8px;
      padding: 6px 0; border-bottom: 1px solid var(--border);
    }
    .action-item:last-child { border-bottom: none; }
    .action-priority {
      font-size: 8px; font-weight: 800; padding: 2px 6px; border-radius: 4px;
      text-transform: uppercase; letter-spacing: 0.05em; flex-shrink: 0; margin-top: 1px;
    }
    .priority-critical { background: rgba(239,68,68,0.1); color: #ef4444; }
    .priority-high { background: rgba(245,158,11,0.1); color: #f59e0b; }
    .priority-medium { background: rgba(37,99,235,0.1); color: #2563eb; }
    .priority-low { background: rgba(16,185,129,0.1); color: #10b981; }
    .action-body { display: flex; flex-direction: column; }
    .action-title { font-size: 11px; font-weight: 600; color: var(--text-primary); }
    .action-category { font-size: 10px; color: var(--text-muted); margin-top: 1px; }

    /* Suggestions */
    .suggestions-bar {
      display: flex; gap: 8px; padding: 12px 20px;
      overflow-x: auto; border-top: 1px solid var(--border); background: var(--card-bg);
    }
    .suggestions-bar::-webkit-scrollbar { height: 0; }
    .suggestion-chip {
      display: flex; align-items: center; gap: 6px;
      padding: 6px 14px; border: 1px solid var(--command-border);
      border-radius: 20px; background: var(--command-bg);
      color: var(--text-secondary); font-size: 12px;
      white-space: nowrap; cursor: pointer; transition: all 0.15s ease;
    }
    .suggestion-chip:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-bg); }
    .chip-icon { color: var(--text-muted); }
    .suggestion-chip:hover .chip-icon { color: var(--accent); }

    /* Input */
    .input-bar {
      display: flex; align-items: center; gap: 10px;
      padding: 14px 20px; background: var(--card-bg); border-top: 1px solid var(--border);
    }
    .attach-btn {
      display: flex; align-items: center; justify-content: center;
      width: 36px; height: 36px; border: 1px solid var(--border);
      border-radius: 8px; background: var(--command-bg);
      color: var(--text-muted); cursor: pointer; transition: all 0.15s ease; flex-shrink: 0;
    }
    .attach-btn:hover { border-color: var(--accent); color: var(--accent); }
    .attach-btn:disabled { opacity: 0.6; cursor: wait; }
    .spin-icon { animation: spin 1.2s linear infinite; }
    @keyframes spin { to { transform: rotate(360deg); } }
    .chat-input {
      flex: 1; padding: 10px 14px; border: 1px solid var(--border);
      border-radius: 8px; background: var(--bg); color: var(--text-primary);
      font-size: 14px; outline: none; transition: border-color 0.15s ease;
    }
    .chat-input::placeholder { color: var(--text-muted); }
    .chat-input:focus { border-color: var(--accent); }
    .send-btn {
      display: flex; align-items: center; justify-content: center;
      width: 36px; height: 36px; border: none; border-radius: 8px;
      background: var(--border); color: var(--text-muted);
      cursor: not-allowed; transition: all 0.15s ease; flex-shrink: 0;
    }
    .send-btn.active { background: var(--accent); color: #ffffff; cursor: pointer; }
    .send-btn.active:hover { opacity: 0.9; }

    /* Factor explanations */
    .factor-row-group { display: flex; flex-direction: column; gap: 2px; }
    .factor-explanation {
      font-size: 10px; color: var(--text-muted); line-height: 1.4;
      margin: 0 0 4px 128px;
    }
    .hall-explanation {
      font-size: 10px; color: var(--text-muted); line-height: 1.4;
      margin-top: 2px; max-width: 220px;
    }

    /* Hallucination Alert Banner */
    .hallucination-banner {
      display: flex; align-items: flex-start; justify-content: space-between;
      padding: 10px 14px; border-radius: 8px; margin-bottom: 12px;
      animation: fadeIn 0.3s ease; flex-shrink: 0;
    }
    .banner-high {
      background: rgba(239,68,68,0.08); border: 1px solid rgba(239,68,68,0.2);
    }
    .banner-medium {
      background: rgba(245,158,11,0.08); border: 1px solid rgba(245,158,11,0.2);
    }
    .banner-content { display: flex; align-items: flex-start; gap: 10px; flex: 1; }
    .banner-icon { flex-shrink: 0; margin-top: 1px; }
    .banner-high .banner-icon { color: #ef4444; }
    .banner-medium .banner-icon { color: #f59e0b; }
    .banner-text { display: flex; flex-direction: column; gap: 2px; }
    .banner-title {
      font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.03em;
    }
    .banner-high .banner-title { color: #ef4444; }
    .banner-medium .banner-title { color: #f59e0b; }
    .banner-desc { font-size: 11px; color: var(--text-secondary); line-height: 1.5; }
    .banner-dismiss {
      background: none; border: none; cursor: pointer;
      color: var(--text-muted); padding: 2px; flex-shrink: 0; opacity: 0.6;
      transition: opacity 0.15s;
    }
    .banner-dismiss:hover { opacity: 1; }

    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
  `
})
export class ChatComponent implements AfterViewChecked {
  @ViewChild('chatFeed') private chatFeed!: ElementRef;
  private api = inject(ApiService);

  newMessage = '';
  isTyping = false;
  isUploading = false;
  backendConnected = false;
  showHallucinationBanner = false;
  hallucinationBannerRating: 'medium' | 'high' | null = null;
  hallucinationBannerScore = 0;
  private shouldScroll = false;
  private sessionId = 'session_' + Date.now();

  suggestionChips: string[] = [
    'What is the total insured value?',
    'List all coverage gaps',
    'Summarize the loss history',
    'What endorsements are included?'
  ];

  messages: (ChatMessage & { _expanded?: boolean })[] = [
    {
      id: 1,
      role: 'ai',
      content: 'Welcome! I\'m your AI underwriting companion. Upload documents using the paperclip button below or from the Documents tab, then ask me anything about them. I\'ll provide answers grounded in your documents with full hallucination analysis.',
      timestamp: this.getCurrentTime(),
    }
  ];

  private nextId = 2;

  constructor() {
    this.api.healthCheck().subscribe({
      next: (res) => { this.backendConnected = res.status === 'ok'; },
      error: () => { this.backendConnected = false; },
    });
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  onFileSelect(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;
    const files = Array.from(input.files);
    input.value = '';

    for (const file of files) {
      this.uploadSingleFile(file);
    }
  }

  private uploadSingleFile(file: File): void {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!ext || !['pdf', 'docx', 'doc'].includes(ext)) {
      this.messages.push({
        id: this.nextId++,
        role: 'ai',
        content: `Unsupported file type: .${ext}. Please upload PDF or DOCX files.`,
        timestamp: this.getCurrentTime(),
      });
      this.shouldScroll = true;
      return;
    }

    this.isUploading = true;
    this.messages.push({
      id: this.nextId++,
      role: 'ai',
      content: `Uploading and indexing ${file.name}...`,
      timestamp: this.getCurrentTime(),
    });
    this.shouldScroll = true;

    this.api.uploadDocument(file).subscribe({
      next: (res) => {
        this.isUploading = false;
        this.messages.push({
          id: this.nextId++,
          role: 'ai',
          content: `${res.filename} uploaded successfully! Indexed ${res.num_chunks} chunks from ${res.num_pages} pages. You can now ask questions about this document.`,
          timestamp: this.getCurrentTime(),
        });
        this.shouldScroll = true;
      },
      error: (err) => {
        this.isUploading = false;
        const errorMsg = err.error?.detail || 'Upload failed. Please try again.';
        this.messages.push({
          id: this.nextId++,
          role: 'ai',
          content: `Upload failed for ${file.name}: ${errorMsg}`,
          timestamp: this.getCurrentTime(),
        });
        this.shouldScroll = true;
      },
    });
  }

  sendMessage(): void {
    const text = this.newMessage.trim();
    if (!text || this.isTyping) return;

    this.messages.push({
      id: this.nextId++,
      role: 'user',
      content: text,
      timestamp: this.getCurrentTime(),
    });

    this.newMessage = '';
    this.shouldScroll = true;
    this.callBackend(text);
  }

  sendSuggestion(chip: string): void {
    if (this.isTyping) return;
    this.messages.push({
      id: this.nextId++,
      role: 'user',
      content: chip,
      timestamp: this.getCurrentTime(),
    });
    this.shouldScroll = true;
    this.callBackend(chip);
  }

  private callBackend(query: string): void {
    this.isTyping = true;
    this.shouldScroll = true;

    this.api.chat(query, this.sessionId).subscribe({
      next: (res) => {
        this.isTyping = false;
        this.messages.push({
          id: this.nextId++,
          role: 'ai',
          content: res.answer,
          timestamp: this.getCurrentTime(),
          hallucination: res.hallucination as any,
          actions: res.actions as any,
          sources: res.sources,
          _expanded: false,
        });

        // Show hallucination banner for medium/high risk
        const rating = (res.hallucination as any)?.rating;
        if (rating === 'medium' || rating === 'high') {
          this.showHallucinationBanner = true;
          this.hallucinationBannerRating = rating;
          this.hallucinationBannerScore = (res.hallucination as any).overall_score;
        } else {
          this.showHallucinationBanner = false;
        }

        this.shouldScroll = true;
      },
      error: (err) => {
        this.isTyping = false;
        const errorMsg = err.status === 0
          ? 'Backend is not running. Start the server with: cd backend && python3 main.py'
          : err.error?.detail || 'Something went wrong. Please try again.';
        this.messages.push({
          id: this.nextId++,
          role: 'ai',
          content: errorMsg,
          timestamp: this.getCurrentTime(),
        });
        this.shouldScroll = true;
      },
    });
  }

  // ─── Hallucination helpers ───
  getHallColor(h: HallucinationReport): string {
    if (h.overall_score >= 80) return '#10b981';
    if (h.overall_score >= 50) return '#f59e0b';
    return '#ef4444';
  }

  getHallBadgeBg(h: HallucinationReport): string {
    if (h.overall_score >= 80) return 'rgba(16,185,129,0.12)';
    if (h.overall_score >= 50) return 'rgba(245,158,11,0.12)';
    return 'rgba(239,68,68,0.12)';
  }

  getHallLabel(h: HallucinationReport): string {
    if (h.overall_score >= 80) return 'Well Grounded';
    if (h.overall_score >= 50) return 'Partially Grounded';
    return 'Low Grounding';
  }

  getFactorColor(value: number): string {
    if (value >= 80) return '#10b981';
    if (value >= 50) return '#f59e0b';
    return '#ef4444';
  }

  getFactorDisplayLabel(key: string): string {
    const labels: Record<string, string> = {
      'retrieval_confidence': 'Source Relevance',
      'response_grounding': 'Answer Accuracy',
      'numerical_fidelity': 'Number Accuracy',
      'entity_consistency': 'Name & Term Accuracy',
    };
    return labels[key] ?? key;
  }

  getFactorExplanation(key: string, value: number): string {
    const explanations: Record<string, Record<string, string>> = {
      'retrieval_confidence': {
        high: 'The AI found highly relevant passages in your documents.',
        medium: 'The AI found some relevant information, but the match was partial.',
        low: 'The AI struggled to find closely matching information.',
      },
      'response_grounding': {
        high: 'The answer closely follows what is stated in the source documents.',
        medium: 'Parts of the answer go beyond what the documents explicitly state.',
        low: 'Much of the answer is not directly supported by the documents.',
      },
      'numerical_fidelity': {
        high: 'Numbers and dollar amounts in the answer match the source documents.',
        medium: 'Some numbers may not exactly match the source documents.',
        low: 'Numbers in the answer may be inaccurate or unsupported.',
      },
      'entity_consistency': {
        high: 'Names, companies, and key terms are used correctly.',
        medium: 'Some names or terms may not perfectly match the sources.',
        low: 'Names or key terms in the answer may be incorrect.',
      },
    };
    const tier = value >= 80 ? 'high' : value >= 50 ? 'medium' : 'low';
    return explanations[key]?.[tier] ?? '';
  }

  getHallLabelExplanation(h: HallucinationReport): string {
    if (h.overall_score >= 80) return 'This answer is well supported by your uploaded documents.';
    if (h.overall_score >= 50) return 'Parts of this answer may go beyond what the documents say.';
    return 'This answer has limited support from your documents. Verify key claims.';
  }

  dismissHallucinationBanner(): void {
    this.showHallucinationBanner = false;
  }

  onChatFeedScroll(): void {
    if (this.showHallucinationBanner) {
      this.showHallucinationBanner = false;
    }
  }

  formatCategory(cat: string): string {
    return cat.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }

  private scrollToBottom(): void {
    try {
      const el = this.chatFeed.nativeElement;
      el.scrollTop = el.scrollHeight;
    } catch (err) {}
  }

  private getCurrentTime(): string {
    return new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
  }
}
