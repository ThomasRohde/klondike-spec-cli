import { PlayCircleIcon } from '@heroicons/react/24/solid';

interface SessionBannerProps {
    sessionNumber: number;
    focus: string;
    date: string;
}

export function SessionBanner({ sessionNumber, focus, date }: SessionBannerProps) {
    return (
        <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white px-4 py-2 shadow-md">
            <div className="max-w-7xl mx-auto flex items-center justify-between gap-4 flex-wrap">
                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                        <PlayCircleIcon className="w-5 h-5 animate-pulse" />
                        <span className="font-semibold">Session #{sessionNumber}</span>
                    </div>
                    <span className="hidden sm:inline text-green-100">|</span>
                    <span className="hidden sm:inline text-white/90 truncate max-w-md">
                        {focus}
                    </span>
                </div>
                <div className="flex items-center gap-3">
                    <span className="text-sm text-green-100">
                        Started: {date}
                    </span>
                    <div className="w-2 h-2 bg-white rounded-full animate-pulse" />
                </div>
            </div>
        </div>
    );
}
