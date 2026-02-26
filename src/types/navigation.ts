// Navigation types

import type { LucideIcon } from 'lucide-react';

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  badge?: number;
}

export interface NavSection {
  title: string;
  items: NavItem[];
}
