export interface Language {
  code: string;
  name: string;
  native: string;
}

export const SUPPORTED_LANGUAGES: Language[] = [
  // Indian Languages (important for your audience)
  { code: 'hi',    name: 'Hindi',          native: 'हिन्दी' },
  { code: 'ta',    name: 'Tamil',          native: 'தமிழ்' },
  { code: 'te',    name: 'Telugu',         native: 'తెలుగు' },
  { code: 'kn',    name: 'Kannada',        native: 'ಕನ್ನಡ' },
  { code: 'ml',    name: 'Malayalam',      native: 'മലയാളം' },
  { code: 'mr',    name: 'Marathi',        native: 'मराठी' },
  { code: 'bn',    name: 'Bengali',        native: 'বাংলা' },
  { code: 'gu',    name: 'Gujarati',       native: 'ગુજરાતી' },
  { code: 'pa',    name: 'Punjabi',        native: 'ਪੰਜਾਬੀ' },
  { code: 'ur',    name: 'Urdu',           native: 'اردو' },
  
  // Global Languages
  { code: 'en-US', name: 'English (US)',   native: 'English (US)' },
  { code: 'en-GB', name: 'English (UK)',   native: 'English (UK)' },
  { code: 'en-IN', name: 'English (India)',native: 'English (India)' },
  { code: 'zh',    name: 'Chinese',        native: '中文' },
  { code: 'ja',    name: 'Japanese',       native: '日本語' },
  { code: 'ko',    name: 'Korean',         native: '한국어' },
  { code: 'ar',    name: 'Arabic',         native: 'العربية' },
  { code: 'fr',    name: 'French',         native: 'Français' },
  { code: 'de',    name: 'German',         native: 'Deutsch' },
  { code: 'es',    name: 'Spanish',        native: 'Español' },
  { code: 'pt',    name: 'Portuguese',     native: 'Português' },
  { code: 'it',    name: 'Italian',        native: 'Italiano' },
  { code: 'ru',    name: 'Russian',        native: 'Русский' },
  { code: 'tr',    name: 'Turkish',        native: 'Türkçe' },
  { code: 'nl',    name: 'Dutch',          native: 'Nederlands' },
  { code: 'pl',    name: 'Polish',         native: 'Polski' },
  { code: 'sv',    name: 'Swedish',        native: 'Svenska' },
  { code: 'da',    name: 'Danish',         native: 'Dansk' },
  { code: 'fi',    name: 'Finnish',        native: 'Suomi' },
  { code: 'no',    name: 'Norwegian',      native: 'Norsk' },
  { code: 'id',    name: 'Indonesian',     native: 'Bahasa Indonesia' },
  { code: 'ms',    name: 'Malay',          native: 'Bahasa Melayu' },
  { code: 'th',    name: 'Thai',           native: 'ภาษาไทย' },
  { code: 'vi',    name: 'Vietnamese',     native: 'Tiếng Việt' },
];
