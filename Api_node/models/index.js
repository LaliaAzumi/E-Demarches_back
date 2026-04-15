/**
 * Export centralisé de tous les modèles
 * Architecture MVC - Modèles
 */

const { sequelize } = require('../config/database');
const Notification = require('./notification.model');
const Demande = require('./demande.model');

// Relations entre modèles (si nécessaire)
// Demande.hasMany(Notification);
// Notification.belongsTo(Demande);

const models = {
  Notification,
  Demande,
  sequelize
};

module.exports = models;
