/**
 * Routes pour les Notifications
 * Architecture MVC - Routes
 */

const express = require('express');
const router = express.Router();
const NotificationController = require('../controllers/notification.controller');
const { authMiddleware, requireRole } = require('../middleware/auth.middleware');

// Toutes les routes nécessitent une authentification
router.use(authMiddleware);

// GET /notifications - Récupérer toutes les notifications
router.get('/', NotificationController.getAll);

// GET /notifications/non-lues - Notifications non lues
router.get('/non-lues', NotificationController.getNonLues);

// GET /notifications/compteur - Nombre de notifications non lues
router.get('/compteur', NotificationController.getCompteur);

// GET /notifications/:id - Une notification spécifique
router.get('/:id', NotificationController.getById);

// POST /notifications - Créer (admin/agents uniquement)
router.post('/', requireRole('agent', 'administrateur'), NotificationController.create);

// POST /notifications/:id/marquer-lu - Marquer comme lue
router.post('/:id/marquer-lu', NotificationController.marquerLu);

// POST /notifications/marquer-tout-lu - Tout marquer comme lu
router.post('/marquer-tout-lu', NotificationController.marquerToutLu);

// DELETE /notifications/:id - Supprimer
router.delete('/:id', NotificationController.delete);

// POST /notifications/envoyer-groupe - Envoi groupé (admin/agents)
router.post('/envoyer-groupe', requireRole('agent', 'administrateur'), NotificationController.envoyerGroupe);

// POST /notifications/notify - Endpoint pour Python (notifications temps réel)
// Ce endpoint est appelé par le backend Python pour émettre des notifications WebSocket
router.post('/notify', NotificationController.notifyWebSocket);

module.exports = router;
