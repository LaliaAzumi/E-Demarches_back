/**
 * Service Demandes - communique avec API Django
 * Gestion des demandes via Django (source de vérité)
 */

const apiClient = require('./apiClient.service');

class DemandeService {
  /**
   * Récupère toutes les demandes avec filtres
   */
  static async getAll(token, filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.statut) params.append('statut', filters.statut);
    if (filters.type_demande) params.append('type_demande', filters.type_demande);
    if (filters.page) params.append('page', filters.page);
    if (filters.limit) params.append('limit', filters.limit);
    
    const queryString = params.toString();
    const endpoint = `/demandes/${queryString ? '?' + queryString : ''}`;
    
    return apiClient.get(endpoint, token);
  }

  /**
   * Récupère une demande par ID
   */
  static async getById(id, token) {
    return apiClient.get(`/demandes/${id}/`, token);
  }

  /**
   * Crée une demande
   */
  static async create(data, token) {
    return apiClient.post('/demandes/', token, data);
  }

  /**
   * Met à jour une demande
   */
  static async update(id, data, token) {
    return apiClient.put(`/demandes/${id}/`, token, data);
  }

  /**
   * Change le statut d'une demande
   */
  static async changerStatut(id, data, token) {
    return apiClient.post(`/demandes/${id}/changer_statut/`, token, data);
  }

  /**
   * Supprime une demande
   */
  static async delete(id, token) {
    return apiClient.delete(`/demandes/${id}/`, token);
  }

  /**
   * Récupère les statistiques
   */
  static async getStatistiques(token) {
    return apiClient.get('/demandes/statistiques/', token);
  }

  /**
   * Demandes en attente
   */
  static async getATraiter(token) {
    return apiClient.get('/demandes/a_traiter/', token);
  }

  /**
   * Mes demandes (citoyen connecté)
   */
  static async getMesDemandes(token) {
    return apiClient.get('/demandes/mes_demandes/', token);
  }
}

module.exports = DemandeService;
