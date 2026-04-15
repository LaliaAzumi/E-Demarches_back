/**
 * Routes pour les Demandes
 * Architecture MVC - Routes
 */

const express = require('express');
const router = express.Router();
const DemandeController = require('../controllers/demande.controller');
const { authMiddleware, requireRole } = require('../middleware/auth.middleware');

// Toutes les routes nécessitent une authentification
router.use(authMiddleware);

// GET /demandes - Liste avec filtres
router.get('/', DemandeController.getAll);

// GET /demandes/statistiques - Statistiques (agents/admins)
router.get('/statistiques', requireRole('agent', 'administrateur'), DemandeController.getStatistiques);

// GET /demandes/a-traiter - Demandes en attente (agents/admins)
router.get('/a-traiter', requireRole('agent', 'administrateur'), DemandeController.getATraiter);

// GET /demandes/mes-demandes - Mes demandes (citoyen)
router.get('/mes-demandes', DemandeController.getMesDemandes);

// POST /demandes - Créer une demande
router.post('/', DemandeController.create);

// GET /demandes/:id - Une demande spécifique
router.get('/:id', DemandeController.getById);

// PUT /demandes/:id - Mettre à jour
router.put('/:id', DemandeController.update);

// POST /demandes/:id/changer-statut - Changer statut (agents/admins)
router.post('/:id/changer-statut', requireRole('agent', 'administrateur'), DemandeController.changerStatut);

// DELETE /demandes/:id - Supprimer
router.delete('/:id', DemandeController.delete);

module.exports = router;
