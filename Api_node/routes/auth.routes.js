/**
 * Routes pour l'Authentification (JWT + OAuth Google)
 * Architecture MVC - Routes
 */

const express = require('express');
const router = express.Router();
const AuthController = require('../controllers/auth.controller');
const { authMiddleware } = require('../middleware/auth.middleware');

// POST /auth/login - Connexion email/password
router.post('/login', AuthController.login);

// POST /auth/register - Inscription
router.post('/register', AuthController.register);

// POST /auth/google - Connexion Google OAuth
router.post('/google', AuthController.googleAuth);

// POST /auth/google/verify - Vérifier token Google
router.post('/google/verify', AuthController.verifyGoogle);

// POST /auth/refresh - Rafraîchir token JWT
router.post('/refresh', AuthController.refresh);

// POST /auth/logout - Déconnexion (protégé)
router.post('/logout', authMiddleware, AuthController.logout);

// GET /auth/me - Profil utilisateur (protégé)
router.get('/me', authMiddleware, AuthController.me);

module.exports = router;
