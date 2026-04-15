/**
 * Demande Controller - MVC Controller
 * Gère les demandes via API Django (pas de DB direct)
 */

const DemandeService = require('../services/demande.service');
const NotificationService = require('../services/notification.service');

class DemandeController {
  /**
   * GET /demandes
   * Récupère les demandes via Django
   */
  static async getAll(req, res) {
    try {
      const token = req.token;
      const filters = req.query;
      
      const data = await DemandeService.getAll(token, filters);
      
      res.json(data);
    } catch (error) {
      console.error('[DemandeController] getAll error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la récupération des demandes'
      });
    }
  }

  /**
   * GET /demandes/:id
   */
  static async getById(req, res) {
    try {
      const { id } = req.params;
      const token = req.token;
      
      const data = await DemandeService.getById(id, token);
      
      if (!data.success && data.status === 404) {
        return res.status(404).json(data);
      }
      
      res.json(data);
    } catch (error) {
      console.error('[DemandeController] getById error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la récupération'
      });
    }
  }

  /**
   * POST /demandes
   * Crée via Django + notifie WebSocket
   */
  static async create(req, res) {
    try {
      const token = req.token;
      const data = req.body;
      
      const result = await DemandeService.create(data, token);
      
      if (result.success && result.data) {
        // Notifier le citoyen via WebSocket
        if (req.io) {
          const userId = req.user.id;
          req.io.to(`user_${userId}`).emit('demande_creee', result.data);
          
          // Créer notification via Django
          await NotificationService.create({
            utilisateur_id: userId,
            type_notification: 'compte_cree',
            message: `Votre demande ${result.data.id_demande} a été créée.`
          }, token);
        }
      }
      
      res.status(result.success ? 201 : 400).json(result);
    } catch (error) {
      console.error('[DemandeController] create error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la création'
      });
    }
  }

  /**
   * PUT /demandes/:id
   */
  static async update(req, res) {
    try {
      const { id } = req.params;
      const token = req.token;
      const data = req.body;
      
      const result = await DemandeService.update(id, data, token);
      
      if (!result.success && result.status === 404) {
        return res.status(404).json(result);
      }
      
      res.json(result);
    } catch (error) {
      console.error('[DemandeController] update error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la mise à jour'
      });
    }
  }

  /**
   * POST /demandes/:id/changer-statut
   * Change statut via Django + notifie WebSocket
   */
  static async changerStatut(req, res) {
    try {
      const { id } = req.params;
      const token = req.token;
      const { statut, motif } = req.body;
      
      const result = await DemandeService.changerStatut(id, { statut, motif }, token);
      
      // Notifier changement via WebSocket
      if (result.success && req.io && result.data) {
        // Récupérer l'utilisateur du citoyen (via les données de la demande)
        const demande = result.data;
        const citoyenUserId = demande.citoyen?.utilisateur?.id;
        
        if (citoyenUserId) {
          const messages = {
            'en_cours': `Votre demande ${demande.id_demande} est en cours de traitement.`,
            'validee': `Votre demande ${demande.id_demande} a été validée !`,
            'rejetee': `Votre demande ${demande.id_demande} a été rejetée.`
          };
          
          // Émettre événement statut changé
          req.io.to(`user_${citoyenUserId}`).emit('demande_statut_change', {
            demande_id: demande.id,
            id_demande: demande.id_demande,
            statut: statut,
            motif: motif
          });
          
          // Créer notification
          await NotificationService.create({
            utilisateur_id: citoyenUserId,
            type_notification: 'changement_statut',
            message: messages[statut] || 'Statut mis à jour'
          }, token);
          
          // Émettre notification temps réel
          req.io.to(`user_${citoyenUserId}`).emit('notification_alert', {
            type: 'changement_statut',
            message: messages[statut]
          });
        }
      }
      
      res.json(result);
    } catch (error) {
      console.error('[DemandeController] changerStatut error:', error);
      res.status(400).json({
        success: false,
        message: error.message || 'Erreur lors du changement de statut'
      });
    }
  }

  /**
   * DELETE /demandes/:id
   */
  static async delete(req, res) {
    try {
      const { id } = req.params;
      const token = req.token;
      
      const result = await DemandeService.delete(id, token);
      
      if (!result.success && result.status === 404) {
        return res.status(404).json(result);
      }
      
      res.json(result);
    } catch (error) {
      console.error('[DemandeController] delete error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la suppression'
      });
    }
  }

  /**
   * GET /demandes/statistiques
   */
  static async getStatistiques(req, res) {
    try {
      const token = req.token;
      
      const result = await DemandeService.getStatistiques(token);
      res.json(result);
    } catch (error) {
      console.error('[DemandeController] getStatistiques error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors du calcul des statistiques'
      });
    }
  }

  /**
   * GET /demandes/a-traiter
   */
  static async getATraiter(req, res) {
    try {
      const token = req.token;
      
      const result = await DemandeService.getATraiter(token);
      res.json(result);
    } catch (error) {
      console.error('[DemandeController] getATraiter error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la récupération'
      });
    }
  }

  /**
   * GET /demandes/mes-demandes
   */
  static async getMesDemandes(req, res) {
    try {
      const token = req.token;
      
      const result = await DemandeService.getMesDemandes(token);
      res.json(result);
    } catch (error) {
      console.error('[DemandeController] getMesDemandes error:', error);
      res.status(500).json({
        success: false,
        message: 'Erreur lors de la récupération'
      });
    }
  }
}

module.exports = DemandeController;
