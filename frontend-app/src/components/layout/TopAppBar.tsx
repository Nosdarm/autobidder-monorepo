import React from 'react';
import { useTheme } from 'next-themes';
import { useTranslation } from 'react-i18next';
import { Sun, Moon, Monitor, Languages, Menu } from 'lucide-react'; // Added Menu

import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface TopAppBarProps {
  pageTitle?: string;
  onMenuToggle?: () => void;
}

export default function TopAppBar({ pageTitle, onMenuToggle }: TopAppBarProps) {
  const { t, i18n } = useTranslation();
  const { setTheme } = useTheme();

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
  };
  
  // Use translated pageTitle if provided, otherwise default to translated "Dashboard"
  const currentTitle = pageTitle || t('topAppBar.defaultTitle', 'Dashboard');


  return (
    <header className="bg-card border-b p-4 flex items-center justify-between h-16">
      <button 
        onClick={onMenuToggle} 
        className="md:hidden p-2 text-foreground hover:bg-muted rounded-md"
        aria-label={t('topAppBar.toggleMenuAriaLabel')}
      >
        <Menu className="h-6 w-6" /> {/* Using Lucide Menu icon */}
      </button>
      
      <div className="flex-1 md:ml-4">
        <h1 className="text-xl font-semibold text-foreground">{currentTitle}</h1>
      </div>
      
      <div className="flex items-center space-x-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon" aria-label={t('topAppBar.languageSwitcherAriaLabel')}>
              <Languages className="h-[1.2rem] w-[1.2rem]" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => changeLanguage('en')} disabled={i18n.resolvedLanguage === 'en'}>
              {t('topAppBar.languageEnglish')}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => changeLanguage('es')} disabled={i18n.resolvedLanguage === 'es'}>
              {t('topAppBar.languageSpanish')}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="icon" aria-label={t('topAppBar.themeSwitcherAriaLabel')}>
              <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
              <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
              <span className="sr-only">{t('topAppBar.themeSwitcherSrOnly')}</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => setTheme('light')}>
              <Sun className="mr-2 h-4 w-4" />
              {t('topAppBar.themeLight')}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme('dark')}>
              <Moon className="mr-2 h-4 w-4" />
              {t('topAppBar.themeDark')}
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => setTheme('system')}>
              <Monitor className="mr-2 h-4 w-4" />
              {t('topAppBar.themeSystem')}
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
