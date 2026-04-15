/**
 * Configuration de la base de données PostgreSQL avec Sequelize
 */

const { Sequelize } = require('sequelize');
require('dotenv').config();

const sequelize = new Sequelize(
  process.env.DB_NAME,
  process.env.DB_USER,
  process.env.DB_PASSWORD,
  {
    host: process.env.DB_HOST,
    port: process.env.DB_PORT || 5432,
    dialect: 'postgres',
    logging: process.env.NODE_ENV === 'development' ? console.log : false,
    pool: {
      max: 5,
      min: 0,
      acquire: 30000,
      idle: 10000
    }
  }
);

// Test de connexion
const testConnection = async () => {
  try {
    await sequelize.authenticate();
    console.log('✅ Connexion à PostgreSQL établie avec succès.');
  } catch (error) {
    console.error('❌ Impossible de se connecter à la base de données:', error);
  }
};

module.exports = { sequelize, testConnection };
