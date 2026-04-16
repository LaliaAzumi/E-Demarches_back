/**
 * Serveur Node.js + Express
 * API Gateway pour Notifications et Demandes (WebSocket + Proxy Django)
 * Architecture MVC - Pas de DB directe, communique avec API Django
 * 
 * NOTIFICATIONS TEMPS RÉEL:
 *   - WebSocket pour notifications instantanées frontend
 *   - Python appelle POST /api/notifications/notify pour émettre
 *   - Rooms: user_{id}, agents, admins
 */

const express = require('express');
const cors = require('cors');
const http = require('http');
const socketIo = require('socket.io');
require('dotenv').config();

const authRoutes = require('./routes/auth.routes');
const notificationRoutes = require('./routes/notification.routes');
const demandeRoutes = require('./routes/demande.routes');

// Import du service WebSocket
const WebSocketService = require('./services/websocket.service');

// Initialisation Express
const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: process.env.FRONTEND_URL || 'http://localhost:5173',
    methods: ['GET', 'POST'],
    credentials: true
  }
});

// Instance du service WebSocket
const websocketService = new WebSocketService(io);

// Middleware
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:5173',
  credentials: true
}));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Middleware pour injecter io et websocketService dans les requêtes
app.use((req, res, next) => {
  req.io = io;
  req.websocketService = websocketService;
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

// WebSocket - Gestion des connexions avancée
io.on('connection', (socket) => {
  console.log('🔌 Client WebSocket connecté:', socket.id);
  
  // Authentification WebSocket - attend les infos utilisateur
  socket.on('authenticate', (userData) => {
    if (userData && userData.userId) {
      websocketService.handleConnection(socket, userData);
      socket.emit('authenticated', { success: true, userId: userData.userId });
    } else {
      socket.emit('authenticated', { success: false, error: 'Données utilisateur manquantes' });
    }
  });
  
  // Rejoindre une room utilisateur (legacy, utiliser authenticate)
  socket.on('join', (userId) => {
    socket.join(`user_${userId}`);
    console.log(`👤 Utilisateur ${userId} a rejoint sa room`);
    websocketService.connectedUsers.set(userId, socket.id);
  });
  
  // Quitter une room
  socket.on('leave', (userId) => {
    socket.leave(`user_${userId}`);
    console.log(`👤 Utilisateur ${userId} a quitté sa room`);
  });
  
  // Accusé de lecture notification
  socket.on('notification_read', (data) => {
    const userId = Array.from(websocketService.connectedUsers.entries())
      .find(([_, socketId]) => socketId === socket.id)?.[0];
    if (userId) {
      websocketService.handleNotificationRead(userId, data.notificationId);
    }
  });
  
  // Ping/Pong pour vérifier la connexion
  socket.on('ping', () => {
    socket.emit('pong', { timestamp: Date.now() });
  });
  
  // Déconnexion
  socket.on('disconnect', () => {
    // Trouver et supprimer l'utilisateur déconnecté
    for (const [userId, socketId] of websocketService.connectedUsers.entries()) {
      if (socketId === socket.id) {
        websocketService.handleDisconnection(userId);
        break;
      }
    }
    console.log('🔌 Client WebSocket déconnecté:', socket.id);
  });
});

// Exposer websocketService globalement pour les contrôleurs
app.set('websocketService', websocketService);

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
      console.log(`📡 WebSocket temps réel actif sur ws://localhost:${PORT}`);
      console.log(`🔗 API Gateway (proxy vers Django):`);
      console.log(`   - Notifications REST: http://localhost:${PORT}/api/notifications`);
      console.log(`   - Notifications WebSocket: émet via POST /api/notifications/notify`);
      console.log(`   - Demandes: http://localhost:${PORT}/api/demandes`);
      console.log(`🔌 WebSocket Rooms: user_{id}, agents, admins\n`);
    });
  } catch (error) {
    console.error('❌ Erreur démarrage serveur:', error);
    process.exit(1);
  }
};

startServer();

module.exports = { app, io };
