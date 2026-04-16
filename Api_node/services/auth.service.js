/**
 * Service Authentification - communique avec API Django OAuth
 * Gestion de l'authentification JWT et OAuth Google via Django
 */

const apiClient = require('./apiClient.service');

class AuthService {
  /**
   * Authentification avec email/mot de passe (via Django)
   */
  static async login(credentials) {
    return apiClient.post('/auth/login/', null, credentials);
  }

  /**
   * Inscription standard (via Django)
   */
  static async register(data) {
    return apiClient.post('/auth/register/', null, data);
  }

  /**
   * Authentification Google OAuth
   * @param {string} accessToken - Token d'accès Google
   */
  static async googleLogin(accessToken) {
    return apiClient.post('/auth/google/login/', null, {
      access_token: accessToken
    });
  }

  /**
   * Vérifier un token Google (sans créer de session)
   */
  static async verifyGoogleToken(accessToken) {
    return apiClient.post('/auth/google/verify/', null, {
      access_token: accessToken
    });
  }

  /**
   * Rafraîchir le token JWT
   */
  static async refreshToken(refreshToken) {
    return apiClient.post('/auth/refresh/', null, {
      refresh: refreshToken
    });
  }

  /**
   * Déconnexion
   */
  static async logout(token) {
    return apiClient.post('/auth/logout/', token);
  }

  /**
   * Récupérer le profil utilisateur connecté
   */
  static async getMe(token) {
    return apiClient.get('/auth/me/', token);
  }
}

module.exports = AuthService;
