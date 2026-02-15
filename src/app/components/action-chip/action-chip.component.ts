import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-action-chip',
  standalone: true,
  template: `
    <button class="chip">{{ label }}</button>
  `,
  styles: [`
    .chip {
      white-space: nowrap;
      padding: 0.5rem 1rem;
      border-radius: 9999px;
      border: 1px solid var(--border);
      background: var(--chip-bg);
      color: var(--text-muted);
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      cursor: pointer;
      transition: all 0.3s ease;
    }
    .chip:hover {
      color: var(--accent);
      border-color: var(--accent-muted);
      background: var(--chip-hover-bg);
    }
  `]
})
export class ActionChipComponent {
  @Input() label: string = '';
}
