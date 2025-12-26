import { PlayCircleIcon } from '@heroicons/react/24/solid';

interface SessionBannerProps {
    sessionNumber: number;
    focus: string;
    date: string;
}

export function SessionBanner({ sessionNumber, focus, date }: SessionBannerProps) {
    return (
        <div className="session-banner">
            <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap w-full">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        <div className="session-banner-pulse" />
                        <PlayCircleIcon className="w-5 h-5" />
                        <span className="font-display font-semibold">
                            Session #{sessionNumber}
                        </span>
                    </div>
                    <div className="deco-diamond hidden sm:block" style={{ width: 6, height: 6 }} />
                    <span className="hidden sm:inline truncate max-w-md opacity-90">
                        {focus}
                    </span>
                </div>
                <div className="flex items-center gap-3">
                    <span className="text-sm opacity-80">
                        Started: {date}
                    </span>
                </div>
            </div>
        </div>
    );
}
