import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { LucideAngularModule } from 'lucide-angular';

@Component({
  selector: 'app-nav-item',
  standalone: true,
  imports: [CommonModule, LucideAngularModule],
  template: `
    <button
      class="nav-item"
      [class.active]="active"
    >
      <lucide-icon [name]="icon" [size]="20"></lucide-icon>
      <div *ngIf="active" class="nav-indicator"></div>
    </button>
  `,
  styles: [`
    :host { display: block; }
    .nav-item {
      padding: 0.75rem;
      border-radius: 0.75rem;
      transition: all 0.3s ease;
      position: relative;
      color: var(--nav-icon);
      background: transparent;
      border: none;
      cursor: pointer;
    }
    .nav-item:hover { color: var(--nav-icon-hover); }
    .nav-item.active {
      color: var(--accent);
      background: var(--nav-active-bg);
    }
    .nav-indicator {
      position: absolute;
      right: -24px;
      top: 50%;
      transform: translateY(-50%);
      width: 3px;
      height: 20px;
      background: var(--accent);
      border-radius: 3px 0 0 3px;
      box-shadow: 0 0 12px var(--accent);
    }
  `]
})
export class NavItemComponent {
  @Input() icon: string = 'activity';
  @Input() active: boolean = false;
}
