/**
 * Auth Controller - MVC Controller
 * Gère l'authentification (JWT et OAuth Google) via API Django
 */

const AuthService = require('../services/auth.service');

class AuthController {
  /**
   * POST /auth/login
   * Connexion avec email/mot de passe
   */
  static async login(req, res) {
    try {
      const { email, password } = req.body;
      
      if (!email || !password) {
        return res.status(400).json({
          success: false,
          message: 'Email et mot de passe requis'
        });
      }
      
      const result = await AuthService.login({ email, password });
      
      // Émettre événement de connexion via WebSocket si succès
      if (result.success && result.user && req.io) {
        req.io.to(`user_${result.user.id}`).emit('user_login', {
          user_id: result.user.id,
          email: result.user.email,
          timestamp: new Date().toISOString()
        });
      }
      
      res.json(result);
    } catch (error) {
      console.error('[AuthController] login error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la connexion'
      });
    }
  }

  /**
   * POST /auth/register
   * Inscription nouvel utilisateur
   */
  static async register(req, res) {
    try {
      const result = await AuthService.register(req.body);
      res.status(result.success ? 201 : 400).json(result);
    } catch (error) {
      console.error('[AuthController] register error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de l\'inscription'
      });
    }
  }

  /**
   * POST /auth/google
   * Connexion avec Google OAuth
   */
  static async googleAuth(req, res) {
    try {
      const { access_token, id_token } = req.body;
      
      if (!access_token) {
        return res.status(400).json({
          success: false,
          message: 'Token d\'accès Google requis'
        });
      }
      
      const result = await AuthService.googleLogin(access_token);
      
      // Notifier via WebSocket si connexion réussie
      if (result.success && result.user && req.io) {
        const eventType = result.is_new_user ? 'user_registered' : 'user_login';
        req.io.to(`user_${result.user.id}`).emit(eventType, {
          user_id: result.user.id,
          email: result.user.email,
          provider: 'google',
          is_new_user: result.is_new_user || false,
          timestamp: new Date().toISOString()
        });
        
        // Notification pour nouvel utilisateur
        if (result.is_new_user) {
          req.io.to(`user_${result.user.id}`).emit('notification_alert', {
            type: 'welcome',
            message: 'Bienvenue ! Votre compte a été créé avec succès.'
          });
        }
      }
      
      res.json(result);
    } catch (error) {
      console.error('[AuthController] googleAuth error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de l\'authentification Google'
      });
    }
  }

  /**
   * POST /auth/google/verify
   * Vérifier un token Google (sans créer de session)
   */
  static async verifyGoogle(req, res) {
    try {
      const { access_token } = req.body;
      
      if (!access_token) {
        return res.status(400).json({
          success: false,
          message: 'Token d\'accès Google requis'
        });
      }
      
      const result = await AuthService.verifyGoogleToken(access_token);
      res.json(result);
    } catch (error) {
      console.error('[AuthController] verifyGoogle error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la vérification du token'
      });
    }
  }

  /**
   * POST /auth/refresh
   * Rafraîchir le token JWT
   */
  static async refresh(req, res) {
    try {
      const { refresh } = req.body;
      
      if (!refresh) {
        return res.status(400).json({
          success: false,
          message: 'Refresh token requis'
        });
      }
      
      const result = await AuthService.refreshToken(refresh);
      res.json(result);
    } catch (error) {
      console.error('[AuthController] refresh error:', error);
      res.status(401).json({
        success: false,
        message: 'Token invalide ou expiré'
      });
    }
  }

  /**
   * POST /auth/logout
   * Déconnexion
   */
  static async logout(req, res) {
    try {
      const token = req.token;
      const result = await AuthService.logout(token);
      
      // Notifier déconnexion via WebSocket
      if (req.io && req.user) {
        req.io.to(`user_${req.user.id}`).emit('user_logout', {
          user_id: req.user.id,
          timestamp: new Date().toISOString()
        });
      }
      
      res.json(result);
    } catch (error) {
      console.error('[AuthController] logout error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la déconnexion'
      });
    }
  }

  /**
   * GET /auth/me
   * Profil de l'utilisateur connecté
   */
  static async me(req, res) {
    try {
      const token = req.token;
      const result = await AuthService.getMe(token);
      res.json(result);
    } catch (error) {
      console.error('[AuthController] me error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la récupération du profil'
      });
    }
  }
}

module.exports = AuthController;
