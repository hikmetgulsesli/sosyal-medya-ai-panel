'use client';

import { Platform, PlatformLabels, PlatformColors } from '@/types/scheduler';
import { Twitter, Linkedin, Instagram } from 'lucide-react';

interface PlatformBadgeProps {
  platform: Platform;
  showIcon?: boolean;
}

const PlatformIcon = ({ platform }: { platform: Platform }) => {
  const iconClass = "h-3.5 w-3.5";
  
  switch (platform) {
    case 'twitter':
      return <Twitter className={iconClass} />;
    case 'linkedin':
      return <Linkedin className={iconClass} />;
    case 'instagram':
      return <Instagram className={iconClass} />;
    case 'bluesky':
      return (
        <svg className={iconClass} viewBox="0 0 24 24" fill="currentColor">
          <path d="M12 10.8c-1.087-2.114-4.046-6.053-6.798-7.995C2.566.944 1.561 1.266.902 1.565.139 1.908 0 2.98 0 3.725c0 .234.003 1.052.063 1.674.17 1.673.637 4.326 2.49 7.005C4.377 15.07 7.298 17.68 12 21c4.702-3.32 7.623-5.93 9.447-8.596 1.853-2.679 2.32-5.332 2.49-7.005.06-.622.063-1.44.063-1.674 0-.745-.139-1.817-.902-2.16-.659-.299-1.664-.621-4.3.24-2.752 1.942-5.711 5.881-6.798 7.995z" />
        </svg>
      );
    default:
      return null;
  }
};

export function PlatformBadge({ platform, showIcon = true }: PlatformBadgeProps) {
  const color = PlatformColors[platform];
  
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium"
      style={{
        backgroundColor: `${color}15`,
        color: color,
      }}
    >
      {showIcon && <PlatformIcon platform={platform} />}
      {PlatformLabels[platform]}
    </span>
  );
}
