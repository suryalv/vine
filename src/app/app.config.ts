import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideHttpClient } from '@angular/common/http';
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
  AlertTriangle,
  CheckCircle,
  Info,
  Eye,
  Trash2,
  RefreshCw,
  X,
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
  AlertTriangle,
  CheckCircle,
  Info,
  Eye,
  Trash2,
  RefreshCw,
  X,
};

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideHttpClient(),
    {
      provide: LUCIDE_ICONS,
      multi: true,
      useValue: new LucideIconProvider(icons),
    },
  ],
};
