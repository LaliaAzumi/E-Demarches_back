/**
 * Notification Controller - MVC Controller
 * Gère les notifications via API Django (pas de DB direct)
 */

const NotificationService = require('../services/notification.service');

class NotificationController {
  /**
   * GET /notifications
   * Récupère toutes les notifications via Django
   */
  static async getAll(req, res) {
    try {
      const token = req.token;
      const data = await NotificationService.getAll(token);
      
      // Émettre aux clients WebSocket connectés
      if (req.io && data.success && data.data) {
        const userId = req.user.id;
        req.io.to(`user_${userId}`).emit('notifications_list', data.data);
      }
      
      res.json(data);
    } catch (error) {
      console.error('[NotificationController] getAll error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la récupération des notifications'
      });
    }
  }

  /**
   * GET /notifications/non-lues
   */
  static async getNonLues(req, res) {
    try {
      const token = req.token;
      const data = await NotificationService.getNonLues(token);
      res.json(data);
    } catch (error) {
      console.error('[NotificationController] getNonLues error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la récupération'
      });
    }
  }

  /**
   * GET /notifications/compteur
   */
  static async getCompteur(req, res) {
    try {
      const token = req.token;
      const data = await NotificationService.countNonLues(token);
      
      // Émettre le compteur en temps réel
      if (req.io && data.success) {
        const userId = req.user.id;
        req.io.to(`user_${userId}`).emit('notification_count', data.data);
      }
      
      res.json(data);
    } catch (error) {
      console.error('[NotificationController] getCompteur error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors du comptage'
      });
    }
  }

  /**
   * GET /notifications/:id
   */
  static async getById(req, res) {
    try {
      const { id } = req.params;
      const token = req.token;
      
      const data = await NotificationService.getById(id, token);
      
      if (!data.success && data.status === 404) {
        return res.status(404).json(data);
      }
      
      res.json(data);
    } catch (error) {
      console.error('[NotificationController] getById error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la récupération'
      });
    }
  }

  /**
   * POST /notifications
   * Crée via Django + émet WebSocket
   */
  static async create(req, res) {
    try {
      const token = req.token;
      const data = req.body;
      
      const result = await NotificationService.create(data, token);
      
      // Émettre via WebSocket si création réussie
      if (result.success && result.data && req.io) {
        const utilisateurId = data.utilisateur_id;
        req.io.to(`user_${utilisateurId}`).emit('nouvelle_notification', result.data);
        req.io.to(`user_${utilisateurId}`).emit('notification_alert', {
          message: data.message,
          type: data.type_notification || 'autre'
        });
      }
      
      res.status(result.success ? 201 : 400).json(result);
    } catch (error) {
      console.error('[NotificationController] create error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la création'
      });
    }
  }

  /**
   * POST /notifications/:id/marquer-lu
   */
  static async marquerLu(req, res) {
    try {
      const { id } = req.params;
      const token = req.token;
      
      const result = await NotificationService.marquerLu(id, token);
      
      // Mettre à jour le compteur en temps réel
      if (result.success && req.io) {
        const userId = req.user.id;
        const countData = await NotificationService.countNonLues(token);
        req.io.to(`user_${userId}`).emit('notification_count', countData.data);
      }
      
      res.json(result);
    } catch (error) {
      console.error('[NotificationController] marquerLu error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la mise à jour'
      });
    }
  }

  /**
   * POST /notifications/marquer-tout-lu
   */
  static async marquerToutLu(req, res) {
    try {
      const token = req.token;
      
      const result = await NotificationService.marquerToutLu(token);
      
      // Reset du compteur en temps réel
      if (result.success && req.io) {
        const userId = req.user.id;
        req.io.to(`user_${userId}`).emit('notification_count', { non_lues: 0 });
      }
      
      res.json(result);
    } catch (error) {
      console.error('[NotificationController] marquerToutLu error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la mise à jour'
      });
    }
  }

  /**
   * DELETE /notifications/:id
   */
  static async delete(req, res) {
    try {
      const { id } = req.params;
      const token = req.token;
      
      const result = await NotificationService.delete(id, token);
      res.json(result);
    } catch (error) {
      console.error('[NotificationController] delete error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la suppression'
      });
    }
  }

  /**
   * POST /notifications/envoyer-groupe
   */
  static async envoyerGroupe(req, res) {
    try {
      const token = req.token;
      const data = req.body;
      
      const result = await NotificationService.envoyerGroupe(data, token);
      
      // Émettre à tous les destinataires
      if (result.success && req.io && data.utilisateur_ids) {
        data.utilisateur_ids.forEach(userId => {
          req.io.to(`user_${userId}`).emit('nouvelle_notification', {
            message: data.message,
            type: data.type_notification
          });
        });
      }
      
      res.json(result);
    } catch (error) {
      console.error('[NotificationController] envoyerGroupe error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de l\'envoi'
      });
    }
  }
}

module.exports = NotificationController;
