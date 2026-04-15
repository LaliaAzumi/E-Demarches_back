/**
 * Service Notifications - communique avec API Django
 * Gestion des notifications via Django (source de vérité)
 */

const apiClient = require('./apiClient.service');

class NotificationService {
  /**
   * Récupère toutes les notifications d'un utilisateur
   */
  static async getAll(token) {
    return apiClient.get('/notifications/', token);
  }

  /**
   * Récupère les notifications non lues
   */
  static async getNonLues(token) {
    return apiClient.get('/notifications/non_lues/', token);
  }

  /**
   * Compte les notifications non lues
   */
  static async countNonLues(token) {
    return apiClient.get('/notifications/compteur/', token);
  }

  /**
   * Récupère une notification par ID
   */
  static async getById(id, token) {
    return apiClient.get(`/notifications/${id}/`, token);
  }

  /**
   * Crée une notification (via Django)
   */
  static async create(data, token) {
    return apiClient.post('/notifications/', token, data);
  }

  /**
   * Marque une notification comme lue
   */
  static async marquerLu(id, token) {
    return apiClient.post(`/notifications/${id}/marquer_lu/`, token);
  }

  /**
   * Marque toutes les notifications comme lues
   */
  static async marquerToutLu(token) {
    return apiClient.post('/notifications/marquer_tout_lu/', token);
  }

  /**
   * Supprime une notification
   */
  static async delete(id, token) {
    return apiClient.delete(`/notifications/${id}/`, token);
  }

  /**
   * Envoie une notification groupée
   */
  static async envoyerGroupe(data, token) {
    return apiClient.post('/notifications/envoyer_a_tous/', token, data);
  }
}

module.exports = NotificationService;
