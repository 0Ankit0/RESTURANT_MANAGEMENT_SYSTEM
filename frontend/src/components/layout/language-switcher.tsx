'use client';

import { useState } from 'react';
import { Globe } from 'lucide-react';


const LANGUAGES = [
  { code: 'en', name: 'English' },
  { code: 'es', name: 'Español' },
  { code: 'fr', name: 'Français' },
];

export function LanguageSwitcher() {
  const [language, setLanguage] = useState('en');

  const [isOpen, setIsOpen] = useState(false);

  const handleLanguageChange = (code: string) => {
    setLanguage(code);
    setIsOpen(false);
    // In a real app with backend i18n, we would set a cookie or header here
    // document.cookie = `fastapi_language=${value}; path=/; SameSite=Lax`;
    // window.location.reload();
  };

  const currentLanguage = LANGUAGES.find(l => l.code === language);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 px-3 py-2 rounded-lg hover:bg-gray-100"
      >
        <Globe className="h-4 w-4" />
        <span>{currentLanguage?.name}</span>
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 mt-2 w-48 bg-white border border-gray-200 rounded-lg shadow-lg z-20 py-1">
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                onClick={() => handleLanguageChange(lang.code)}
                className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-50 flex items-center justify-between ${
                  language === lang.code ? 'text-blue-600 font-medium' : 'text-gray-700'
                }`}
              >
                {lang.name}
                {language === lang.code && <div className="h-1.5 w-1.5 rounded-full bg-blue-600" />}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
