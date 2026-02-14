import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import {
  LUCIDE_ICONS,
  LucideIconProvider,
  Activity,
  FileText,
  Layers,
  Target,
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  ArrowUpRight,
  ChevronRight,
  Zap,
  Paperclip,
  Send,
  Upload,
} from 'lucide-angular';

const icons = {
  Activity,
  FileText,
  Layers,
  Target,
  Sparkles,
  ShieldAlert,
  ShieldCheck,
  ArrowUpRight,
  ChevronRight,
  Zap,
  Paperclip,
  Send,
  Upload,
};

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    {
      provide: LUCIDE_ICONS,
      multi: true,
      useValue: new LucideIconProvider(icons),
    },
  ],
};
