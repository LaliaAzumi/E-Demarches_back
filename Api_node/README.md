# API Node.js - Notifications & Demandes

API REST en Node.js + Express pour gérer les notifications et demandes administratives.
Architecture MVC complète.

## 📁 Structure MVC

```
Api_node/
├── config/
│   └── database.js          # Configuration PostgreSQL
├── controllers/             # Contrôleurs MVC
│   ├── notification.controller.js
│   └── demande.controller.js
├── middleware/             # Middlewares
│   └── auth.middleware.js  # Authentification JWT
├── models/                 # Modèles MVC
│   ├── index.js
│   ├── notification.model.js
│   └── demande.model.js
├── routes/                 # Routes API
│   ├── notification.routes.js
│   └── demande.routes.js
├── utils/                  # Utilitaires
│   └── socket.utils.js     # WebSocket
├── .env                    # Variables d'environnement
├── .env.example
├── server.js               # Point d'entrée
└── package.json
```

## 🚀 Installation

```bash
cd back/Api_node
npm install
```

## ⚙️ Configuration

Copier `.env.example` vers `.env` et configurer:

```env
PORT=3000
DB_HOST=localhost
DB_PORT=5432
DB_NAME=administration_db
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe
JWT_SECRET=votre_secret_jwt
FRONTEND_URL=http://localhost:5173
```

## ▶️ Démarrage

```bash
# Mode développement (avec auto-reload)
npm run dev

# Mode production
npm start
```

## 🔌 API Endpoints

### Notifications

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/notifications` | Liste des notifications |
| GET | `/api/notifications/non-lues` | Non lues |
| GET | `/api/notifications/compteur` | Compteur non lues |
| GET | `/api/notifications/:id` | Détail |
| POST | `/api/notifications` | Créer (admin/agent) |
| POST | `/api/notifications/:id/marquer-lu` | Marquer lue |
| POST | `/api/notifications/marquer-tout-lu` | Tout marquer lu |
| DELETE | `/api/notifications/:id` | Supprimer |
| POST | `/api/notifications/envoyer-groupe` | Envoi groupé |

### Demandes

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| GET | `/api/demandes` | Liste avec filtres |
| GET | `/api/demandes/statistiques` | Stats (admin/agent) |
| GET | `/api/demandes/a-traiter` | En attente |
| GET | `/api/demandes/mes-demandes` | Mes demandes |
| POST | `/api/demandes` | Créer |
| GET | `/api/demandes/:id` | Détail |
| PUT | `/api/demandes/:id` | Modifier |
| POST | `/api/demandes/:id/changer-statut` | Changer statut |
| DELETE | `/api/demandes/:id` | Supprimer |

## 🔐 Authentification

Toutes les routes nécessitent un token JWT dans le header:

```
Authorization: Bearer <token>
```

## 📡 WebSocket

Connexion temps réel pour les notifications:

```javascript
const socket = io('http://localhost:3000');

// Rejoindre sa room
socket.emit('join', userId);

// Écouter les notifications
socket.on('nouvelle_notification', (data) => {
  console.log('Nouvelle notif:', data);
});
```

## 🛠️ Technologies

- **Express** - Framework web
- **Sequelize** - ORM PostgreSQL
- **Socket.io** - WebSocket temps réel
- **JWT** - Authentification
- **CORS** - Cross-origin
- **Dotenv** - Variables d'environnement
