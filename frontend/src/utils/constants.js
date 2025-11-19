// API Configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

// Status configurations
export const STATUS_CONFIG = {
  completed: { color: 'success', label: 'Completed' },
  quote_generated: { color: 'success', label: 'Quote Generated' },
  in_progress: { color: 'warning', label: 'In Progress' },
  paused: { color: 'warning', label: 'Paused' },
  failed: { color: 'error', label: 'Failed' },
  negotiating: { color: 'info', label: 'Negotiating' },
  message_sent: { color: 'info', label: 'Message Sent' },
};

// Intent configurations
export const INTENT_CONFIG = {
  get_quote: { label: 'Get Quote', icon: '📄' },
  negotiate: { label: 'Negotiate', icon: '🤝' },
  check_status: { label: 'Check Status', icon: '📊' },
};

// Quick templates for new conversations
export const QUICK_TEMPLATES = [
  {
    id: 'quote_organic_cotton',
    title: 'Request Quote - Organic Cotton',
    template: 'I need a quote for 5,000 meters of organic cotton canvas',
  },
  {
    id: 'quote_denim',
    title: 'Request Quote - Denim',
    template: "What's your price for 10k yards of denim fabric?",
  },
  {
    id: 'quote_poplin',
    title: 'Request Quote - Poplin',
    template: 'Cost for cotton poplin 120gsm, GOTS certified?',
  },
  {
    id: 'negotiate_price',
    title: 'Negotiate - Price Reduction',
    template: 'Your quoted price is too high, can we discuss a better rate?',
  },
  {
    id: 'negotiate_leadtime',
    title: 'Negotiate - Lead Time',
    template: 'Can you improve the lead time from 60 to 45 days?',
  },
];

// Pagination defaults
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;