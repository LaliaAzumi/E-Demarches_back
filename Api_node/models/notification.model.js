/**
 * Modèle Notification - MVC Model
 * Gère les notifications utilisateurs
 */

const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const Notification = sequelize.define('Notification', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  utilisateur_id: {
    type: DataTypes.INTEGER,
    allowNull: false,
    references: {
      model: 'utilisateurs',
      key: 'id'
    }
  },
  message: {
    type: DataTypes.TEXT,
    allowNull: false
  },
  type_notification: {
    type: DataTypes.ENUM(
      'changement_statut',
      'dossier_pret',
      'rdv_propose',
      'rdv_confirme',
      'rdv_annule',
      'nouveau_document',
      'compte_cree',
      'autre'
    ),
    defaultValue: 'autre'
  },
  lu: {
    type: DataTypes.BOOLEAN,
    defaultValue: false
  },
  date_envoi: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW
  },
  date_lecture: {
    type: DataTypes.DATE,
    allowNull: true
  },
  lien: {
    type: DataTypes.STRING(500),
    allowNull: true
  },
  icon: {
    type: DataTypes.STRING(50),
    allowNull: true
  }
}, {
  tableName: 'notifications',
  timestamps: true,
  createdAt: 'created_at',
  updatedAt: 'updated_at',
  indexes: [
    { fields: ['utilisateur_id', 'lu'] },
    { fields: ['date_envoi'] },
    { fields: ['type_notification'] }
  ]
});

// Méthodes de classe
Notification.findNonLues = function(utilisateurId) {
  return this.findAll({
    where: {
      utilisateur_id: utilisateurId,
      lu: false
    },
    order: [['date_envoi', 'DESC']]
  });
};

Notification.countNonLues = function(utilisateurId) {
  return this.count({
    where: {
      utilisateur_id: utilisateurId,
      lu: false
    }
  });
};

Notification.marquerToutLu = function(utilisateurId) {
  return this.update(
    { 
      lu: true, 
      date_lecture: new Date() 
    },
    {
      where: {
        utilisateur_id: utilisateurId,
        lu: false
      }
    }
  );
};

// Méthodes d'instance
Notification.prototype.marquerLu = async function() {
  this.lu = true;
  this.date_lecture = new Date();
  return this.save();
};

Notification.prototype.estRecente = function() {
  const vingtQuatreHeures = 24 * 60 * 60 * 1000;
  return (new Date() - this.date_envoi) < vingtQuatreHeures;
};

module.exports = Notification;
