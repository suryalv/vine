import { Component, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';
import { ActionChipComponent } from '../action-chip/action-chip.component';

@Component({
  selector: 'app-command-bar',
  standalone: true,
  imports: [CommonModule, LucideAngularModule, ActionChipComponent],
  template: `
    <div class="command-bar-container">
      <div class="command-bar-inner">

        <!-- Spotlight Command Bar -->
        <div class="spotlight-wrapper">
          <div class="spotlight-glow"></div>
          <div class="spotlight-bar">
            <div class="zap-icon">
              <lucide-icon name="zap" [size]="20"></lucide-icon>
            </div>
            <input
              type="text"
              placeholder="Ask AI to draft a clause, find gaps, or verify limits..."
              class="spotlight-input"
              (keydown.enter)="onSubmit()"
            />
            <div class="bar-actions">
              <button class="attach-btn">
                <lucide-icon name="paperclip" [size]="18"></lucide-icon>
              </button>
              <button class="send-btn" (click)="onSubmit()">
                <lucide-icon name="send" [size]="18"></lucide-icon>
              </button>
            </div>
          </div>
        </div>

        <!-- Quick Shortcuts -->
        <div class="shortcuts">
          <app-action-chip label="Draft Exclusion"></app-action-chip>
          <app-action-chip label="Check Exposure"></app-action-chip>
          <app-action-chip label="Verify ISO Standard"></app-action-chip>
          <app-action-chip label="Summarize Changes"></app-action-chip>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .command-bar-container {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      padding: 2rem;
      display: flex;
      justify-content: center;
      pointer-events: none;
      z-index: 20;
    }
    .command-bar-inner {
      width: 100%;
      max-width: 42rem;
      pointer-events: auto;
    }
    .spotlight-wrapper { position: relative; }
    .spotlight-glow {
      position: absolute;
      inset: -4px;
      background: linear-gradient(135deg, var(--accent), var(--accent-alt));
      border-radius: 1rem;
      filter: blur(12px);
      opacity: 0.15;
      animation: glow-pulse 3s ease-in-out infinite;
    }
    .spotlight-bar {
      position: relative;
      background: var(--command-bg);
      backdrop-filter: blur(24px);
      border: 1px solid var(--command-border);
      border-radius: 1rem;
      box-shadow: var(--command-shadow);
      padding: 0.5rem;
      display: flex;
      align-items: center;
    }
    .zap-icon {
      padding-left: 1rem;
      padding-right: 0.5rem;
      color: var(--accent);
    }
    .spotlight-input {
      flex: 1;
      background: transparent;
      border: none;
      padding: 1rem 0.5rem;
      font-size: 0.875rem;
      color: var(--text-primary);
      font-weight: 500;
      outline: none;
    }
    .spotlight-input::placeholder { color: var(--text-muted); }
    .bar-actions {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding-right: 0.5rem;
    }
    .attach-btn {
      padding: 0.5rem;
      color: var(--text-muted);
      background: none;
      border: none;
      cursor: pointer;
      transition: color 0.2s;
    }
    .attach-btn:hover { color: var(--text-primary); }
    .send-btn {
      height: 2.5rem;
      width: 2.5rem;
      background: var(--accent);
      border-radius: 0.75rem;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      border: none;
      cursor: pointer;
      box-shadow: 0 4px 16px var(--accent-shadow);
      transition: all 0.2s;
    }
    .send-btn:hover { filter: brightness(1.15); }
    .send-btn:active { transform: scale(0.95); }
    .shortcuts {
      display: flex;
      justify-content: center;
      gap: 0.75rem;
      margin-top: 1rem;
      overflow-x: auto;
      padding-bottom: 0.5rem;
    }
    @keyframes glow-pulse {
      0%, 100% { opacity: 0.15; }
      50% { opacity: 0.3; }
    }
  `]
})
export class CommandBarComponent {
  @Output() analyze = new EventEmitter<void>();

  onSubmit() {
    this.analyze.emit();
  }
}
