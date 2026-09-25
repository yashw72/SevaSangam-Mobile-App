import * as SecureStore from 'expo-secure-store';

const AUTH_TOKEN_KEY = 'sevasangam_auth_token';
const AUTH_SESSION_KEY = 'sevasangam_auth_session';

/**
 * Checks if SecureStore is supported and available in the current environment
 */
const isStoreAvailable = async () => {
  try {
    if (typeof SecureStore.isAvailableAsync === 'function') {
      return await SecureStore.isAvailableAsync();
    }
    return true;
  } catch (error) {
    console.warn('[secureStorage] Availability check failed:', error);
    return false;
  }
};

/**
 * Retrieves the stored auth token
 * @returns {Promise<string|null>}
 */
export const getToken = async () => {
  try {
    const available = await isStoreAvailable();
    if (!available) return null;
    return await SecureStore.getItemAsync(AUTH_TOKEN_KEY);
  } catch (error) {
    console.warn('[secureStorage] Error reading token:', error);
    return null;
  }
};

/**
 * Stores the auth token
 * @param {string} token
 * @returns {Promise<boolean>}
 */
export const setToken = async (token) => {
  try {
    const available = await isStoreAvailable();
    if (!available) return false;
    if (!token) {
      await clearToken();
      return true;
    }
    await SecureStore.setItemAsync(AUTH_TOKEN_KEY, token);
    return true;
  } catch (error) {
    console.warn('[secureStorage] Error setting token:', error);
    return false;
  }
};

/**
 * Clears the stored auth token
 * @returns {Promise<boolean>}
 */
export const clearToken = async () => {
  try {
    const available = await isStoreAvailable();
    if (!available) return false;
    await SecureStore.deleteItemAsync(AUTH_TOKEN_KEY);
    return true;
  } catch (error) {
    console.warn('[secureStorage] Error clearing token:', error);
    return false;
  }
};

/**
 * Stores serialized user session data (role, status, expiry, user details)
 * @param {object} session
 * @returns {Promise<boolean>}
 */
export const setSession = async (session) => {
  try {
    const available = await isStoreAvailable();
    if (!available) return false;
    if (!session) {
      await clearSession();
      return true;
    }
    await SecureStore.setItemAsync(AUTH_SESSION_KEY, JSON.stringify(session));
    return true;
  } catch (error) {
    console.warn('[secureStorage] Error storing session:', error);
    return false;
  }
};

/**
 * Retrieves stored session data
 * @returns {Promise<object|null>}
 */
export const getSession = async () => {
  try {
    const available = await isStoreAvailable();
    if (!available) return null;
    const raw = await SecureStore.getItemAsync(AUTH_SESSION_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch (error) {
    console.warn('[secureStorage] Error reading session:', error);
    return null;
  }
};

/**
 * Clears stored session data
 * @returns {Promise<boolean>}
 */
export const clearSession = async () => {
  try {
    const available = await isStoreAvailable();
    if (!available) return false;
    await SecureStore.deleteItemAsync(AUTH_SESSION_KEY);
    return true;
  } catch (error) {
    console.warn('[secureStorage] Error clearing session:', error);
    return false;
  }
};

/**
 * Generic getter for key-value persistence (e.g. language)
 */
export const getItem = async (key) => {
  try {
    const available = await isStoreAvailable();
    if (!available) return null;
    return await SecureStore.getItemAsync(key);
  } catch (error) {
    console.warn(`[secureStorage] Error getting ${key}:`, error);
    return null;
  }
};

/**
 * Generic setter for key-value persistence
 */
export const setItem = async (key, value) => {
  try {
    const available = await isStoreAvailable();
    if (!available) return false;
    await SecureStore.setItemAsync(key, value);
    return true;
  } catch (error) {
    console.warn(`[secureStorage] Error setting ${key}:`, error);
    return false;
  }
};

/**
 * Generic delete item
 */
export const deleteItem = async (key) => {
  try {
    const available = await isStoreAvailable();
    if (!available) return false;
    await SecureStore.deleteItemAsync(key);
    return true;
  } catch (error) {
    console.warn(`[secureStorage] Error deleting ${key}:`, error);
    return false;
  }
};

export default {
  getToken,
  setToken,
  clearToken,
  setSession,
  getSession,
  clearSession,
  getItem,
  setItem,
  deleteItem,
};
