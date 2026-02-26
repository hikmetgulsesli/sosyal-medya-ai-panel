export interface NavItem {
  label: string;
  href: string;
  icon: string;
}

export interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

export interface MobileMenuProps {
  isOpen: boolean;
  onClose: () => void;
}
