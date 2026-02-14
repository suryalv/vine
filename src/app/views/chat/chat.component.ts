import { Component, ElementRef, ViewChild, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { LucideAngularModule } from 'lucide-angular';
import { ChatMessage } from '../../models/insight.model';

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
        </div>
        <span class="header-subtitle">Underwriting Assistant</span>
      </div>

      <!-- Message Feed -->
      <div class="chat-feed" #chatFeed>
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
        <button class="attach-btn" title="Attach file">
          <lucide-icon name="paperclip" [size]="18"></lucide-icon>
        </button>
        <input
          type="text"
          class="chat-input"
          placeholder="Ask about this submission..."
          [(ngModel)]="newMessage"
          (keydown.enter)="sendMessage()"
        />
        <button
          class="send-btn"
          [class.active]="newMessage.trim().length > 0"
          (click)="sendMessage()"
          [disabled]="newMessage.trim().length === 0"
        >
          <lucide-icon name="send" [size]="18"></lucide-icon>
        </button>
      </div>
    </div>
  `,
  styles: `
    :host {
      display: block;
      height: 100%;
    }

    .chat-container {
      display: flex;
      flex-direction: column;
      height: 100%;
      background: var(--bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      overflow: hidden;
    }

    .chat-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 20px;
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
    }

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .header-icon {
      color: var(--accent);
    }

    .header-title {
      font-size: 15px;
      font-weight: 600;
      color: var(--text-primary);
    }

    .header-subtitle {
      font-size: 12px;
      color: var(--text-muted);
    }

    .chat-feed {
      flex: 1;
      overflow-y: auto;
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .chat-feed::-webkit-scrollbar {
      width: 6px;
    }

    .chat-feed::-webkit-scrollbar-track {
      background: transparent;
    }

    .chat-feed::-webkit-scrollbar-thumb {
      background: var(--border);
      border-radius: 3px;
    }

    .message-row {
      display: flex;
      width: 100%;
    }

    .ai-row {
      justify-content: flex-start;
    }

    .user-row {
      justify-content: flex-end;
    }

    .message-bubble {
      max-width: 75%;
      padding: 12px 16px;
      border-radius: 12px;
      position: relative;
    }

    .ai-bubble {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-left: 3px solid var(--accent);
      border-radius: 4px 12px 12px 4px;
    }

    .user-bubble {
      background: var(--accent-bg);
      border: 1px solid var(--accent-muted);
      color: var(--text-primary);
    }

    .ai-indicator {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-bottom: 8px;
    }

    .ai-indicator-icon {
      color: var(--accent);
    }

    .ai-label {
      font-size: 11px;
      font-weight: 600;
      color: var(--accent);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .message-content {
      font-size: 14px;
      line-height: 1.6;
      color: var(--text-primary);
      margin: 0;
      white-space: pre-wrap;
    }

    .message-time {
      display: block;
      font-size: 11px;
      color: var(--text-muted);
      margin-top: 8px;
    }

    .typing-indicator {
      display: flex;
      gap: 4px;
      padding: 4px 0;
    }

    .dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--text-muted);
      animation: typingBounce 1.4s infinite ease-in-out;
    }

    .dot:nth-child(2) {
      animation-delay: 0.2s;
    }

    .dot:nth-child(3) {
      animation-delay: 0.4s;
    }

    @keyframes typingBounce {
      0%, 80%, 100% {
        opacity: 0.3;
        transform: scale(0.8);
      }
      40% {
        opacity: 1;
        transform: scale(1);
      }
    }

    .suggestions-bar {
      display: flex;
      gap: 8px;
      padding: 12px 20px;
      overflow-x: auto;
      border-top: 1px solid var(--border);
      background: var(--card-bg);
    }

    .suggestions-bar::-webkit-scrollbar {
      height: 0;
    }

    .suggestion-chip {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 6px 14px;
      border: 1px solid var(--command-border);
      border-radius: 20px;
      background: var(--command-bg);
      color: var(--text-secondary);
      font-size: 12px;
      white-space: nowrap;
      cursor: pointer;
      transition: all 0.15s ease;
    }

    .suggestion-chip:hover {
      border-color: var(--accent);
      color: var(--accent);
      background: var(--accent-bg);
    }

    .chip-icon {
      color: var(--text-muted);
    }

    .suggestion-chip:hover .chip-icon {
      color: var(--accent);
    }

    .input-bar {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 14px 20px;
      background: var(--card-bg);
      border-top: 1px solid var(--border);
    }

    .attach-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--command-bg);
      color: var(--text-muted);
      cursor: pointer;
      transition: all 0.15s ease;
      flex-shrink: 0;
    }

    .attach-btn:hover {
      border-color: var(--accent);
      color: var(--accent);
    }

    .chat-input {
      flex: 1;
      padding: 10px 14px;
      border: 1px solid var(--border);
      border-radius: 8px;
      background: var(--bg);
      color: var(--text-primary);
      font-size: 14px;
      outline: none;
      transition: border-color 0.15s ease;
    }

    .chat-input::placeholder {
      color: var(--text-muted);
    }

    .chat-input:focus {
      border-color: var(--accent);
    }

    .send-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 36px;
      height: 36px;
      border: none;
      border-radius: 8px;
      background: var(--border);
      color: var(--text-muted);
      cursor: not-allowed;
      transition: all 0.15s ease;
      flex-shrink: 0;
    }

    .send-btn.active {
      background: var(--accent);
      color: #ffffff;
      cursor: pointer;
    }

    .send-btn.active:hover {
      opacity: 0.9;
    }
  `
})
export class ChatComponent implements AfterViewChecked {
  @ViewChild('chatFeed') private chatFeed!: ElementRef;

  newMessage = '';
  isTyping = false;
  private shouldScroll = false;

  suggestionChips: string[] = [
    'Analyze loss history',
    'Draft exclusion clause',
    'Check aggregate limits',
    'Compare to ISO form'
  ];

  messages: ChatMessage[] = [
    {
      id: 1,
      role: 'ai',
      content: 'I\'ve reviewed the General Liability submission for Acme Manufacturing. Here are my initial findings on the policy structure and risk profile.',
      timestamp: '10:30 AM'
    },
    {
      id: 2,
      role: 'user',
      content: 'What are the key risk factors you\'ve identified in this GL policy?',
      timestamp: '10:31 AM'
    },
    {
      id: 3,
      role: 'ai',
      content: 'Based on my analysis, there are three primary risk factors:\n\n1. Products-Completed Operations exposure is elevated due to their industrial equipment manufacturing line, with a 5-year loss ratio of 68%.\n\n2. The premises liability component shows moderate concern -- the 120,000 sq ft facility hosts frequent third-party vendor visits.\n\n3. Contractual liability exposure is significant given their downstream distribution agreements with limited indemnification clauses.',
      timestamp: '10:32 AM'
    },
    {
      id: 4,
      role: 'user',
      content: 'How does their loss history compare to industry benchmarks?',
      timestamp: '10:34 AM'
    },
    {
      id: 5,
      role: 'ai',
      content: 'Their combined loss ratio of 58% over the past 3 years is slightly above the industry median of 52% for SIC code 3559. However, severity trends are improving -- average claim cost dropped 12% YoY. I recommend applying a 5-7% rate adjustment above manual to account for the products exposure, while crediting the improving frequency trend.',
      timestamp: '10:35 AM'
    }
  ];

  private nextId = 6;

  private aiResponses: string[] = [
    'I\'ve run the analysis. The loss history shows a favorable development pattern over the past 36 months, with reserves coming down by approximately 15%. The frequency of claims has decreased, though severity on products liability remains a concern at $42,000 average per claim.',
    'Looking at the exclusion language, I\'d recommend adding a Products Recall exclusion (CG 21 30) and tightening the Contractual Liability limitation to cover only insured contracts as defined. This would help manage the downstream distribution risk we identified earlier.',
    'The current aggregate limits are set at $2M General Aggregate and $2M Products-Completed Operations Aggregate. Given the exposure base and loss history, I\'d suggest considering a $3M General Aggregate with a $2M Products Aggregate, along with a per-location aggregate endorsement for the satellite warehouse.',
    'Comparing against the ISO CG 00 01 (04/13) form, this policy includes several manuscript endorsements that broaden coverage beyond standard ISO terms. Notably, the blanket additional insured provision and the primary/non-contributory language are more expansive than typical market offerings for this class.',
    'Based on the current submission data, the pricing indication falls within the $85,000-$95,000 range for the GL line. This accounts for the rate adjustment I recommended earlier and reflects the improving loss trend credit. Would you like me to prepare a formal quotation worksheet?'
  ];

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  sendMessage(): void {
    const text = this.newMessage.trim();
    if (!text || this.isTyping) return;

    this.messages.push({
      id: this.nextId++,
      role: 'user',
      content: text,
      timestamp: this.getCurrentTime()
    });

    this.newMessage = '';
    this.shouldScroll = true;

    this.simulateAiResponse();
  }

  sendSuggestion(chip: string): void {
    if (this.isTyping) return;

    this.messages.push({
      id: this.nextId++,
      role: 'user',
      content: chip,
      timestamp: this.getCurrentTime()
    });

    this.shouldScroll = true;
    this.simulateAiResponse();
  }

  private simulateAiResponse(): void {
    this.isTyping = true;
    this.shouldScroll = true;

    const responseIndex = (this.messages.length - 1) % this.aiResponses.length;
    const response = this.aiResponses[responseIndex];

    setTimeout(() => {
      this.isTyping = false;
      this.messages.push({
        id: this.nextId++,
        role: 'ai',
        content: response,
        timestamp: this.getCurrentTime()
      });
      this.shouldScroll = true;
    }, 1500);
  }

  private scrollToBottom(): void {
    try {
      const el = this.chatFeed.nativeElement;
      el.scrollTop = el.scrollHeight;
    } catch (err) {
      // noop
    }
  }

  private getCurrentTime(): string {
    const now = new Date();
    return now.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  }
}
