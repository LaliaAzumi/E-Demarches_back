/**
 * Modèle Demande - MVC Model
 * Gère les demandes administratives
 */

const { DataTypes } = require('sequelize');
const { sequelize } = require('../config/database');

const Demande = sequelize.define('Demande', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  id_demande: {
    type: DataTypes.STRING(20),
    unique: true,
    allowNull: true
  },
  citoyen_id: {
    type: DataTypes.INTEGER,
    allowNull: false,
    references: {
      model: 'citoyens',
      key: 'id'
    }
  },
  service_id: {
    type: DataTypes.INTEGER,
    allowNull: true,
    references: {
      model: 'services_administratifs',
      key: 'id'
    }
  },
  type_demande: {
    type: DataTypes.ENUM(
      'carte_identite',
      'passeport',
      'acte_naissance',
      'acte_mariage',
      'autre'
    ),
    allowNull: false
  },
  statut: {
    type: DataTypes.ENUM(
      'en_attente',
      'en_cours',
      'validee',
      'rejetee'
    ),
    defaultValue: 'en_attente'
  },
  motif_rejet: {
    type: DataTypes.TEXT,
    allowNull: true
  },
  date_demande: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW
  }
}, {
  tableName: 'demandes',
  timestamps: true,
  createdAt: 'created_at',
  updatedAt: 'updated_at',
  hooks: {
    beforeCreate: async (demande) => {
      // Générer un ID unique
      if (!demande.id_demande) {
        const prefix = demande.type_demande.substring(0, 3).toUpperCase();
        const suffix = Math.floor(Math.random() * 1000000).toString().padStart(6, '0');
        demande.id_demande = `${prefix}-${suffix}`;
      }
    }
  }
});

// Méthodes de classe
Demande.statistiquesParStatut = function() {
  return this.findAll({
    attributes: ['statut', [sequelize.fn('COUNT', sequelize.col('id')), 'total']],
    group: ['statut']
  });
};

Demande.statistiquesParType = function() {
  return this.findAll({
    attributes: ['type_demande', [sequelize.fn('COUNT', sequelize.col('id')), 'total']],
    group: ['type_demande']
  });
};

Demande.findByCitoyen = function(citoyenId) {
  return this.findAll({
    where: { citoyen_id: citoyenId },
    order: [['date_demande', 'DESC']]
  });
};

Demande.findEnAttente = function() {
  return this.findAll({
    where: { statut: 'en_attente' },
    order: [['date_demande', 'ASC']]
  });
};

// Méthodes d'instance
Demande.prototype.changerStatut = async function(nouveauStatut, motif = null) {
  // Vérifier les transitions valides
  const transitionsValides = {
    'en_attente': ['en_cours', 'rejetee'],
    'en_cours': ['validee', 'rejetee'],
    'validee': [],
    'rejetee': []
  };
  
  const transitions = transitionsValides[this.statut];
  if (!transitions.includes(nouveauStatut)) {
    throw new Error(`Transition de '${this.statut}' vers '${nouveauStatut}' non autorisée`);
  }
  
  // Vérifier le motif pour rejet
  if (nouveauStatut === 'rejetee' && !motif) {
    throw new Error('Un motif de rejet est requis');
  }
  
  this.statut = nouveauStatut;
  if (nouveauStatut === 'rejetee') {
    this.motif_rejet = motif;
  }
  
  return this.save();
};

Demande.prototype.estEnCours = function() {
  return ['en_attente', 'en_cours'].includes(this.statut);
};

module.exports = Demande;
