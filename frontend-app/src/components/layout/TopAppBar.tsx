import React from 'react';
import { useTheme } from 'next-themes';
import { useTranslation } from 'react-i18next'; // Import useTranslation
import { Sun, Moon, Monitor, Languages } from 'lucide-react'; // Icons for theme toggle

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface TopAppBarProps {
  pageTitle?: string;
  onMenuToggle?: () => void; // For mobile sidebar toggle
}

export default function TopAppBar({ pageTitle = "Dashboard", onMenuToggle }: TopAppBarProps) {
  const { setTheme } = useTheme();
  const { i18n } = useTranslation();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };

  return (
    <header className="bg-card border-b p-4 flex items-center justify-between h-16"> {/* Updated bg and added border */}
      {/* Mobile Menu Toggle */}
      <button 
        onClick={onMenuToggle} 
        className="md:hidden p-2 text-foreground hover:bg-muted rounded-md" // Updated styling
        aria-label="Toggle menu"
      >
        <span className="text-2xl">☰</span> {/* Placeholder Icon, consider Lucide Menu */}
      </button>
      
      <div className="flex-1 md:ml-4"> {/* Allow title to take space but also give space for toggle */}
        <h1 className="text-xl font-semibold text-foreground">{pageTitle}</h1>
      </div>
      
      <div className="flex items-center space-x-2"> {/* Container for Theme and Language Toggles */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon" aria-label="Language switcher">
              <Languages className="h-[1.2rem] w-[1.2rem]" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => changeLanguage('en')} disabled={i18n.resolvedLanguage === 'en'}>
              English
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => changeLanguage('es')} disabled={i18n.resolvedLanguage === 'es'}>
              Español
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon" aria-label="Toggle theme">
              <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span className="sr-only">Toggle theme</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setTheme('light')}>
              <Sun className="mr-2 h-4 w-4" />
              Light
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme('dark')}>
              <Moon className="mr-2 h-4 w-4" />
              Dark
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme('system')}>
              <Monitor className="mr-2 h-4 w-4" />
              System
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
        {/* Global actions or user menu could go here, e.g., <UserNav /> */}
      </div>
    </header>
  );
}
