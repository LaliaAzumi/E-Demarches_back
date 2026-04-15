/**
 * Serveur Node.js + Express
 * API Gateway pour Notifications et Demandes (WebSocket + Proxy Django)
 * Architecture MVC - Pas de DB directe, communique avec API Django
 */

const express = require('express');
const cors = require('cors');
const http = require('http');
const socketIo = require('socket.io');
require('dotenv').config();

const authRoutes = require('./routes/auth.routes');
const notificationRoutes = require('./routes/notification.routes');
const demandeRoutes = require('./routes/demande.routes');

// Initialisation Express
const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:5173',
    methods: ['GET', 'POST']
  }
});

// Middleware
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:5173',
  credentials: true
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Middleware pour injecter io dans les requêtes
app.use((req, res, next) => {
  req.io = io;
  next();
});

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/notifications', notificationRoutes);
app.use('/api/demandes', demandeRoutes);

// Route de base
app.get('/', (req, res) => {
  res.json({
    message: 'API Node.js - Administration Services',
    version: '1.0.0',
    endpoints: {
      auth: {
        login: '/api/auth/login',
        register: '/api/auth/register',
        google: '/api/auth/google',
        refresh: '/api/auth/refresh',
        logout: '/api/auth/logout',
        me: '/api/auth/me'
      },
      notifications: '/api/notifications',
      demandes: '/api/demandes'
    }
  });
});

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Gestion des erreurs 404
app.use((req, res) => {
  res.status(404).json({
    success: false,
    message: 'Route non trouvée'
  });
});

// Gestion des erreurs globales
app.use((err, req, res, next) => {
  console.error('Erreur serveur:', err);
  res.status(500).json({
    success: false,
    message: 'Erreur serveur interne'
  });
});

// WebSocket - Gestion des connexions
io.on('connection', (socket) => {
  console.log('🔌 Client connecté:', socket.id);
  
  // Rejoindre une room utilisateur
  socket.on('join', (userId) => {
    socket.join(`user_${userId}`);
    console.log(`👤 Utilisateur ${userId} a rejoint sa room`);
  });
  
  // Quitter une room
  socket.on('leave', (userId) => {
    socket.leave(`user_${userId}`);
    console.log(`👤 Utilisateur ${userId} a quitté sa room`);
  });
  
  // Déconnexion
  socket.on('disconnect', () => {
    console.log('🔌 Client déconnecté:', socket.id);
  });
});

// Port et démarrage
const PORT = process.env.PORT || 3000;

const startServer = async () => {
  try {
    // Vérifier que DJANGO_API_URL est configurée
    if (!process.env.DJANGO_API_URL) {
      console.error('❌ Erreur: DJANGO_API_URL non définie dans .env');
      process.exit(1);
    }
    
    console.log(`🔗 Connexion à l'API Django: ${process.env.DJANGO_API_URL}`);
    
    // Démarrer serveur
    server.listen(PORT, () => {
      console.log(`\n🚀 Serveur Node.js démarré sur http://localhost:${PORT}`);
      console.log(`📡 WebSocket temps réel actif`);
      console.log(`🔗 API Gateway (proxy vers Django):`);
      console.log(`   - Notifications: http://localhost:${PORT}/api/notifications`);
      console.log(`   - Demandes: http://localhost:${PORT}/api/demandes\n`);
    });
  } catch (error) {
    console.error('❌ Erreur démarrage serveur:', error);
    process.exit(1);
  }
};

startServer();

module.exports = { app, io };
