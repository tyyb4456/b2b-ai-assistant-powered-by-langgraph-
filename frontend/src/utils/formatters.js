import { format, formatDistanceToNow, parseISO } from 'date-fns';

// Format currency
export function formatCurrency(amount, currency = 'USD') {
  if (amount === null || amount === undefined) return 'N/A';
  
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  }).format(amount);
}

// Format date
export function formatDate(date, formatStr = 'MMM dd, yyyy') {
  if (!date) return 'N/A';
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return format(dateObj, formatStr);
  } catch (error) {
    console.error('Date formatting error:', error);
    return 'Invalid date';
  }
}

// Format datetime
export function formatDateTime(date) {
  return formatDate(date, 'MMM dd, yyyy - h:mm a');
}

// Format relative time (e.g., "2 hours ago")
export function formatRelativeTime(date) {
  if (!date) return 'N/A';
  
  try {
    const dateObj = typeof date === 'string' ? parseISO(date) : date;
    return formatDistanceToNow(dateObj, { addSuffix: true });
  } catch (error) {
    console.error('Relative time formatting error:', error);
    return 'Invalid date';
  }
}

// Format number with commas
export function formatNumber(num) {
  if (num === null || num === undefined) return 'N/A';
  return new Intl.NumberFormat('en-US').format(num);
}

// Format percentage
export function formatPercentage(value, decimals = 1) {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(decimals)}%`;
}

// Truncate text
export function truncate(text, maxLength = 100) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

// Format phone number
export function formatPhone(phone) {
  if (!phone) return 'N/A';
  // Remove all non-numeric characters
  const cleaned = phone.replace(/\D/g, '');
  
  // Format as (XXX) XXX-XXXX
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  }
  
  return phone;
}

// Format file size
export function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  if (!bytes) return 'N/A';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

// Format quantity with unit
export function formatQuantity(quantity, unit = '') {
  if (quantity === null || quantity === undefined) return 'N/A';
  
  const formattedNumber = formatNumber(quantity);
  return unit ? `${formattedNumber} ${unit}` : formattedNumber;
}

// Format lead time (days to readable format)
export function formatLeadTime(days) {
  if (!days) return 'N/A';
  
  if (days === 1) return '1 day';
  if (days < 7) return `${days} days`;
  
  const weeks = Math.floor(days / 7);
  const remainingDays = days % 7;
  
  if (remainingDays === 0) {
    return weeks === 1 ? '1 week' : `${weeks} weeks`;
  }
  
  return `${weeks} ${weeks === 1 ? 'week' : 'weeks'} ${remainingDays} ${remainingDays === 1 ? 'day' : 'days'}`;
}