/**
 * Service HTTP Client pour communiquer avec l'API Django
 * Toutes les interactions DB passent par Django
 */

const axios = require('axios');

class ApiClientService {
  constructor() {
    this.baseURL = process.env.DJANGO_API_URL || 'http://localhost:8000/api';
    this.apiKey = process.env.DJANGO_API_KEY;
  }

  /**
   * Crée les headers d'authentification à partir du token utilisateur
   */
  getHeaders(token) {
    const headers = {
      'Content-Type': 'application/json'
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    
    if (this.apiKey) {
      headers['X-API-Key'] = this.apiKey;
    }
    
    return headers;
  }

  /**
   * GET request vers Django
   */
  async get(endpoint, token, params = {}) {
    try {
      const response = await axios.get(`${this.baseURL}${endpoint}`, {
        headers: this.getHeaders(token),
        params
      });
      return response.data;
    } catch (error) {
      console.error(`[API Client] GET ${endpoint} error:`, error.message);
      throw this.handleError(error);
    }
  }

  /**
   * POST request vers Django
   */
  async post(endpoint, token, data = {}) {
    try {
      const response = await axios.post(`${this.baseURL}${endpoint}`, data, {
        headers: this.getHeaders(token)
      });
      return response.data;
    } catch (error) {
      console.error(`[API Client] POST ${endpoint} error:`, error.message);
      throw this.handleError(error);
    }
  }

  /**
   * PUT request vers Django
   */
  async put(endpoint, token, data = {}) {
    try {
      const response = await axios.put(`${this.baseURL}${endpoint}`, data, {
        headers: this.getHeaders(token)
      });
      return response.data;
    } catch (error) {
      console.error(`[API Client] PUT ${endpoint} error:`, error.message);
      throw this.handleError(error);
    }
  }

  /**
   * DELETE request vers Django
   */
  async delete(endpoint, token) {
    try {
      const response = await axios.delete(`${this.baseURL}${endpoint}`, {
        headers: this.getHeaders(token)
      });
      return response.data;
    } catch (error) {
      console.error(`[API Client] DELETE ${endpoint} error:`, error.message);
      throw this.handleError(error);
    }
  }

  /**
   * Gestion des erreurs
   */
  handleError(error) {
    if (error.response) {
      // Erreur HTTP (4xx, 5xx)
      return {
        success: false,
        status: error.response.status,
        message: error.response.data?.message || 'Erreur API Django',
        data: error.response.data
      };
    }
    
    if (error.request) {
      // Pas de réponse
      return {
        success: false,
        message: 'API Django non disponible'
      };
    }
    
    return {
      success: false,
      message: error.message
    };
  }
}

module.exports = new ApiClientService();
