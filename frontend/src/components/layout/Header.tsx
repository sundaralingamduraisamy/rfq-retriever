import { Avatar, AvatarFallback } from '@/components/ui/avatar';

export function Header() {
    const user = JSON.parse(localStorage.getItem("user") || '{"name": "Guest", "role": "Visitor"}');

    return (
        <header className="fixed top-0 left-0 right-0 z-50 h-16 bg-background border-b border-border px-4 flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center">
                <img
                    src="/Stellantis.svg.png"
                    alt="Stellantis"
                    className="h-8 w-auto object-contain"
                    onError={(e) => {
                        // Fallback if image fails, though file exists in public
                        e.currentTarget.style.display = 'none';
                    }}
                />
            </div>

            {/* User Profile */}
            <div className="flex items-center gap-3">
                <div className="text-right hidden sm:block">
                    <p className="text-sm font-medium text-foreground">{user.name}</p>
                    <p className="text-xs text-muted-foreground">{user.role}</p>
                </div>
                <Avatar className="h-9 w-9 border-2 border-primary/20 bg-primary">
                    <AvatarFallback className="bg-primary text-primary-foreground text-sm font-medium">
                        {user.name
                            .split(' ')
                            .map((n) => n[0])
                            .join('')}
                    </AvatarFallback>
                </Avatar>
            </div>
        </header>
    );
}
