/**
 * ============================================================================
 * SERVICE: WebSocket Service
 * RÔLE: Gestion des notifications temps réel
 * 
 * ARCHITECTURE:
 *   Ce service gère les connexions WebSocket pour les notifications temps réel.
 *   Il fait le pont entre le backend Python (REST API) et le frontend ( temps réel).
 * 
 * FONCTIONNEMENT:
 *   1. Python crée une notification (RDV, Demande, etc.)
 *   2. Python appelle l'API Node POST /api/notifications/notify
 *   3. Node émet la notification via WebSocket au(x) destinataire(s)
 *   4. Frontend reçoit la notification instantanément
 * 
 * ROOMS:
 *   - user_{id}: Room privée pour chaque utilisateur
 *   - agent: Room commune pour tous les agents
 *   - admin: Room commune pour les admins
 * 
 * PATTERN: Pub/Sub via WebSocket
 * AGILE: Temps réel = UX fluide et réactive
 * ============================================================================
 */

class WebSocketService {
    constructor(io) {
        this.io = io;
        this.connectedUsers = new Map(); // userId -> socketId
    }

    /**
     * Gère la connexion d'un nouveau client WebSocket
     * 
     * @param {Socket} socket - Instance Socket.io du client
     * @param {Object} userData - Données utilisateur (id, role, etc.)
     */
    handleConnection(socket, userData) {
        const { userId, role } = userData;
        
        // Enregistrer la connexion
        this.connectedUsers.set(userId, socket.id);
        
        // Rejoindre la room privée de l'utilisateur
        socket.join(`user_${userId}`);
        console.log(`👤 Utilisateur ${userId} connecté en temps réel`);
        
        // Rejoindre les rooms selon le rôle
        if (role === 'agent' || role === 'agent') {
            socket.join('agents');
        }
        if (role === 'administrateur') {
            socket.join('admins');
        }

        // Gérer la déconnexion
        socket.on('disconnect', () => {
            this.handleDisconnection(userId);
        });

        // Écouter l'accusé de lecture
        socket.on('notification_read', (data) => {
            this.handleNotificationRead(userId, data.notificationId);
        });
    }

    /**
     * Gère la déconnexion d'un utilisateur
     * 
     * @param {string|number} userId - ID de l'utilisateur
     */
    handleDisconnection(userId) {
        this.connectedUsers.delete(userId);
        console.log(`👤 Utilisateur ${userId} déconnecté du temps réel`);
    }

    /**
     * Envoie une notification à un utilisateur spécifique
     * 
     * @param {string|number} userId - ID du destinataire
     * @param {Object} notification - Données de la notification
     * @returns {boolean} - True si envoyé, False si utilisateur offline
     * 
     * EXEMPLE:
     *   websocketService.notifyUser(123, {
     *     type: 'rdv_propose',
     *     title: 'Nouveau rendez-vous',
     *     message: 'Un agent vous propose un RDV',
     *     data: { rdvId: 456, date: '2026-04-20' }
     *   });
     */
    notifyUser(userId, notification) {
        const isConnected = this.connectedUsers.has(userId);
        
        if (isConnected) {
            this.io.to(`user_${userId}`).emit('notification', {
                ...notification,
                timestamp: new Date().toISOString(),
                delivered: true
            });
            console.log(`📨 Notification envoyée à l'utilisateur ${userId}`);
            return true;
        } else {
            console.log(`📭 Utilisateur ${userId} hors ligne - notification en file d'attente`);
            // TODO: Stocker en DB pour livraison différée
            return false;
        }
    }

    /**
     * Envoie une notification à tous les agents
     * 
     * @param {Object} notification - Données de la notification
     */
    notifyAllAgents(notification) {
        this.io.to('agents').emit('notification', {
            ...notification,
            timestamp: new Date().toISOString(),
            target: 'agents'
        });
        console.log(`📨 Notification envoyée à tous les agents`);
    }

    /**
     * Envoie une notification à tous les admins
     * 
     * @param {Object} notification - Données de la notification
     */
    notifyAllAdmins(notification) {
        this.io.to('admins').emit('notification', {
            ...notification,
            timestamp: new Date().toISOString(),
            target: 'admins'
        });
        console.log(`📨 Notification envoyée aux administrateurs`);
    }

    /**
     * Notifie la création d'un nouveau rendez-vous
     * 
     * @param {number} citoyenId - ID du citoyen concerné
     * @param {Object} rdvData - Données du rendez-vous
     */
    notifyRdvCreated(citoyenId, rdvData) {
        this.notifyUser(citoyenId, {
            type: 'rdv_propose',
            priority: 'high',
            title: '💼 Nouveau rendez-vous proposé',
            message: `Un agent vous propose un rendez-vous le ${rdvData.date}`,
            data: {
                rdvId: rdvData.id,
                demandeId: rdvData.demandeId,
                date: rdvData.date,
                heure: rdvData.heure,
                lieu: rdvData.lieu,
                action: '/rendez-vous/' + rdvData.id
            }
        });
    }

    /**
     * Notifie la confirmation d'un rendez-vous
     * 
     * @param {number} agentId - ID de l'agent concerné
     * @param {Object} rdvData - Données du rendez-vous
     */
    notifyRdvConfirmed(agentId, rdvData) {
        this.notifyUser(agentId, {
            type: 'rdv_confirme',
            priority: 'normal',
            title: '✅ Rendez-vous confirmé',
            message: `Le citoyen a confirmé le rendez-vous du ${rdvData.date}`,
            data: {
                rdvId: rdvData.id,
                demandeId: rdvData.demandeId,
                date: rdvData.date,
                citoyenNom: rdvData.citoyenNom
            }
        });
    }

    /**
     * Notifie le changement de statut d'une demande
     * 
     * @param {number} citoyenId - ID du citoyen
     * @param {Object} demandeData - Données de la demande
     */
    notifyDemandeStatusChange(citoyenId, demandeData) {
        const statusMessages = {
            'en_traitement': 'Votre demande est en cours de traitement',
            'traitee': '🎉 Votre demande a été traitée !',
            'rejetee': '❌ Votre demande a été rejetée',
            'en_attente': '⏳ Votre demande est en attente de documents'
        };

        this.notifyUser(citoyenId, {
            type: 'demande_status',
            priority: demandeData.status === 'traitee' ? 'high' : 'normal',
            title: 'Mise à jour de votre demande',
            message: statusMessages[demandeData.status] || 'Statut mis à jour',
            data: {
                demandeId: demandeData.id,
                reference: demandeData.reference,
                nouveauStatut: demandeData.status,
                action: '/demandes/' + demandeData.id
            }
        });
    }

    /**
     * Notifie les agents d'une nouvelle demande
     * 
     * @param {Object} demandeData - Données de la demande
     */
    notifyNewDemandeToAgents(demandeData) {
        this.notifyAllAgents({
            type: 'nouvelle_demande',
            priority: 'normal',
            title: '📥 Nouvelle demande reçue',
            message: `Demande ${demandeData.reference} en attente d'assignation`,
            data: {
                demandeId: demandeData.id,
                reference: demandeData.reference,
                service: demandeData.service,
                dateSoumission: demandeData.dateSoumission
            }
        });
    }

    /**
     * Gère l'accusé de lecture d'une notification
     * 
     * @param {number} userId - ID de l'utilisateur
     * @param {number} notificationId - ID de la notification
     */
    handleNotificationRead(userId, notificationId) {
        console.log(`👁️ Notification ${notificationId} lue par utilisateur ${userId}`);
        // TODO: Mettre à jour le statut en base via API Python
    }

    /**
     * Vérifie si un utilisateur est connecté en temps réel
     * 
     * @param {number} userId - ID de l'utilisateur
     * @returns {boolean}
     */
    isUserConnected(userId) {
        return this.connectedUsers.has(userId);
    }

    /**
     * Retourne les statistiques de connexion
     * 
     * @returns {Object}
     */
    getStats() {
        return {
            totalConnected: this.connectedUsers.size,
            users: Array.from(this.connectedUsers.keys())
        };
    }
}

module.exports = WebSocketService;
