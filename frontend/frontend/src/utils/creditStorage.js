const TOKEN_KEY = 'citation_checker_token';
const FREE_USAGE_KEY = 'citation_checker_free_used';

// Token management (paid tier)
export const saveToken = (token) => {
  try {
    localStorage.setItem(TOKEN_KEY, token);
  } catch (e) {
    console.error('Failed to save token:', e);
  }
};

export const getToken = () => {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch (e) {
    console.error('Failed to get token:', e);
    return null;
  }
};

export const clearToken = () => {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch (e) {
    console.error('Failed to clear token:', e);
  }
};

// Free tier tracking
export const getFreeUsage = () => {
  try {
    return parseInt(localStorage.getItem(FREE_USAGE_KEY) || '0', 10);
  } catch (e) {
    console.error('Failed to get free usage:', e);
    return 0;
  }
};

export const incrementFreeUsage = (count) => {
  try {
    const current = getFreeUsage();
    localStorage.setItem(FREE_USAGE_KEY, String(current + count));
  } catch (e) {
    console.error('Failed to increment free usage:', e);
  }
};

export const resetFreeUsage = () => {
  try {
    localStorage.removeItem(FREE_USAGE_KEY);
  } catch (e) {
    console.error('Failed to reset free usage:', e);
  }
};