'use client';

import { useMemo } from 'react';
import { ScheduledPost, PlatformColors } from '@/types/scheduler';
import { ChevronLeft, ChevronRight } from 'lucide-react';

interface CalendarViewProps {
  posts: ScheduledPost[];
  currentDate: Date;
  onDateChange: (date: Date) => void;
  onSelectDate: (date: Date) => void;
  selectedDate: Date | null;
}

export function CalendarView({
  posts,
  currentDate,
  onDateChange,
  onSelectDate,
  selectedDate,
}: CalendarViewProps) {
  const { days, monthName, year } = useMemo(() => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();
    
    const days: Array<{
      day: number;
      isCurrentMonth: boolean;
      isToday: boolean;
      posts: ScheduledPost[];
      date: Date;
    }> = [];
    
    // Previous month days
    const prevMonth = new Date(year, month, 0);
    for (let i = startingDayOfWeek - 1; i >= 0; i--) {
      const day = prevMonth.getDate() - i;
      days.push({
        day,
        isCurrentMonth: false,
        isToday: false,
        posts: [],
        date: new Date(year, month - 1, day),
      });
    }
    
    // Current month days
    const today = new Date();
    for (let day = 1; day <= daysInMonth; day++) {
      const date = new Date(year, month, day);
      const dateStr = date.toISOString().split('T')[0];
      const dayPosts = posts.filter((post) => {
        const postDate = new Date(post.scheduledAt).toISOString().split('T')[0];
        return postDate === dateStr;
      });
      
      days.push({
        day,
        isCurrentMonth: true,
        isToday:
          today.getDate() === day &&
          today.getMonth() === month &&
          today.getFullYear() === year,
        posts: dayPosts,
        date,
      });
    }
    
    // Next month days
    const remainingDays = 42 - days.length;
    for (let day = 1; day <= remainingDays; day++) {
      days.push({
        day,
        isCurrentMonth: false,
        isToday: false,
        posts: [],
        date: new Date(year, month + 1, day),
      });
    }
    
    const monthName = firstDay.toLocaleString('default', { month: 'long' });
    
    return { days, monthName, year };
  }, [currentDate, posts]);

  const handlePrevMonth = () => {
    onDateChange(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };

  const handleNextMonth = () => {
    onDateChange(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };

  const handleToday = () => {
    onDateChange(new Date());
  };

  const weekDays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div className="space-y-4">
      {/* Calendar Header */}
      <div className="flex items-center justify-between rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-[var(--text)]">
            {monthName} {year}
          </h2>
          <div className="flex gap-1">
            <button
              onClick={handlePrevMonth}
              className="rounded-lg p-1.5 text-[var(--text-muted)] hover:bg-[var(--secondary)] hover:text-[var(--text)] cursor-pointer"
              style={{ transitionDuration: 'var(--duration-fast)' }}
            >
              <ChevronLeft className="h-5 w-5" />
            </button>
            <button
              onClick={handleNextMonth}
              className="rounded-lg p-1.5 text-[var(--text-muted)] hover:bg-[var(--secondary)] hover:text-[var(--text)] cursor-pointer"
              style={{ transitionDuration: 'var(--duration-fast)' }}
            >
              <ChevronRight className="h-5 w-5" />
            </button>
          </div>
        </div>
        <button
          onClick={handleToday}
          className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-1.5 text-sm font-medium text-[var(--text)] hover:bg-[var(--secondary)] cursor-pointer"
          style={{ transitionDuration: 'var(--duration-fast)' }}
        >
          Today
        </button>
      </div>

      {/* Calendar Grid */}
      <div className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-4">
        {/* Days Header */}
        <div className="mb-2 grid grid-cols-7 gap-2">
          {weekDays.map((day) => (
            <div
              key={day}
              className="py-2 text-center text-sm font-medium text-[var(--text-muted)]"
            >
              {day}
            </div>
          ))}
        </div>

        {/* Calendar Days */}
        <div className="grid grid-cols-7 gap-2">
          {days.map((dayInfo, index) => {
            const isSelected =
              selectedDate &&
              dayInfo.date.toDateString() === selectedDate.toDateString();

            return (
              <button
                key={index}
                onClick={() => onSelectDate(dayInfo.date)}
                className={`min-h-[100px] rounded-lg border p-2 text-left transition-colors cursor-pointer ${
                  dayInfo.isCurrentMonth
                    ? 'border-[var(--border)] bg-[var(--surface)] hover:bg-[var(--secondary)]'
                    : 'border-[var(--border-subtle)] bg-[var(--surface)]/50'
                } ${dayInfo.isToday ? 'ring-2 ring-[var(--primary)]' : ''} ${
                  isSelected ? 'ring-2 ring-[var(--accent)]' : ''
                }`}
                style={{ transitionDuration: 'var(--duration-fast)' }}
              >
                <span
                  className={`text-sm ${
                    dayInfo.isToday
                      ? 'flex h-6 w-6 items-center justify-center rounded-full bg-[var(--primary)] text-white'
                      : dayInfo.isCurrentMonth
                      ? 'text-[var(--text)]'
                      : 'text-[var(--text-muted)]'
                  }`}
                >
                  {dayInfo.day}
                </span>
                {dayInfo.posts.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {dayInfo.posts.slice(0, 3).map((post) => (
                      <div
                        key={post.id}
                        className="rounded px-1.5 py-0.5 text-xs truncate"
                        style={{
                          backgroundColor: `${PlatformColors[post.platform]}20`,
                          color: PlatformColors[post.platform],
                        }}
                      >
                        {post.content.slice(0, 20)}...
                      </div>
                    ))}
                    {dayInfo.posts.length > 3 && (
                      <div className="text-xs text-[var(--text-muted)] px-1.5">
                        +{dayInfo.posts.length - 3} more
                      </div>
                    )}
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
