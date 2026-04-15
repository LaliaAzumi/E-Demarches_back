/**
 * Utilitaires WebSocket pour les notifications temps réel
 */

class SocketUtils {
  constructor(io) {
    this.io = io;
  }

  /**
   * Envoie une notification à un utilisateur spécifique
   */
  envoyerNotification(utilisateurId, notification) {
    this.io.to(`user_${utilisateurId}`).emit('nouvelle_notification', notification);
  }

  /**
   * Envoie une notification à plusieurs utilisateurs
   */
  envoyerNotificationGroupe(utilisateurIds, notification) {
    utilisateurIds.forEach(id => {
      this.envoyerNotification(id, notification);
    });
  }

  /**
   * Envoie à tous les agents
   */
  envoyerAuxAgents(notification) {
    this.io.to('role_agent').emit('notification_agent', notification);
  }

  /**
   * Envoie à tous les admins
   */
  envoyerAuxAdmins(notification) {
    this.io.to('role_administrateur').emit('notification_admin', notification);
  }

  /**
   * Diffuse à tous les clients connectés
   */
  diffuser(message, data) {
    this.io.emit(message, data);
  }

  /**
   * Met à jour le compteur de notifications pour un utilisateur
   */
  actualiserCompteur(utilisateurId, count) {
    this.io.to(`user_${utilisateurId}`).emit('notification_count', { count });
  }

  /**
   * Notifie le changement de statut d'une demande
   */
  notifierChangementStatut(utilisateurId, demande) {
    this.io.to(`user_${utilisateurId}`).emit('demande_statut_change', {
      demande_id: demande.id,
      id_demande: demande.id_demande,
      statut: demande.statut
    });
  }
}

module.exports = SocketUtils;
