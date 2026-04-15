/**
 * Middleware d'authentification JWT
 * Vérifie les tokens et protège les routes
 */

const jwt = require('jsonwebtoken');

const authMiddleware = (req, res, next) => {
  try {
    // Récupérer le token du header
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({
        success: false,
        message: 'Token manquant. Veuillez vous connecter.'
      });
    }
    
    const token = authHeader.substring(7);
    
    // Vérifier le token
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    // Ajouter les infos utilisateur à la requête
    req.user = {
      id: decoded.id,
      email: decoded.email,
      role: decoded.role,
      citoyen_id: decoded.citoyen_id || null,
      agent_id: decoded.agent_id || null
    };
    
    // Stocker le token pour les appels à l'API Django
    req.token = token;
    
    next();
  } catch (error) {
    if (error.name === 'TokenExpiredError') {
      return res.status(401).json({
        success: false,
        message: 'Token expiré. Veuillez vous reconnecter.'
      });
    }
    
    return res.status(401).json({
      success: false,
      message: 'Token invalide'
    });
  }
};

// Middleware pour vérifier les rôles
const requireRole = (...roles) => {
  return (req, res, next) => {
    if (!req.user) {
      return res.status(401).json({
        success: false,
        message: 'Non authentifié'
      });
    }
    
    if (!roles.includes(req.user.role)) {
      return res.status(403).json({
        success: false,
        message: 'Accès refusé. Rôle insuffisant.'
      });
    }
    
    next();
  };
};

module.exports = { authMiddleware, requireRole };
