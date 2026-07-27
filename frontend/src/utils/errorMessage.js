/**
 * Shared API error message utility.
 * Formats API errors (400, 401, 403, 404, 422, 500, network errors) into user-friendly French strings.
 */
export function getErrorMessage(err, options = {}) {
  const { action, resource, fallback } = typeof options === 'string' ? { fallback: options } : options;
  const status = err?.response?.status;
  const data = err?.response?.data;

  // Extract server-provided detail or error string if present
  let serverMessage = null;
  if (data) {
    if (typeof data.detail === 'string') {
      serverMessage = data.detail;
    } else if (typeof data.error === 'string') {
      serverMessage = data.error;
    } else if (typeof data.non_field_errors === 'object' && Array.isArray(data.non_field_errors)) {
      serverMessage = data.non_field_errors.join(' ');
    } else if (typeof data === 'string') {
      serverMessage = data;
    }
  }

  // Handle specific HTTP Status Codes
  if (status === 403) {
    if (action === 'accept' || action === 'accept_recommendation') {
      return "Vous n'êtes pas autorisé à accepter cette recommandation. Seul le responsable du projet peut effectuer cette action.";
    }
    if (action === 'dismiss' || action === 'dismiss_recommendation') {
      return "Vous n'êtes pas autorisé à rejeter cette recommandation. Seul le responsable du projet peut effectuer cette action.";
    }
    if (action === 'generate' || action === 'generate_recommendations') {
      return "Seul le responsable du projet ou un administrateur peut exécuter les diagnostics IA pour ce projet.";
    }
    if (action === 'create_task' || action === 'create') {
      return "Vous n'avez pas la permission de créer cette ressource (réservé au chef de projet).";
    }
    if (action === 'delete') {
      return "Vous n'avez pas la permission d'effectuer cette suppression.";
    }
    return serverMessage || "Accès refusé : vous n'avez pas les permissions requises pour cette action.";
  }

  if (status === 404) {
    if (resource === 'project') {
      return "Ce projet n'existe pas ou vous n'y avez pas accès.";
    }
    if (resource === 'task') {
      return "Cette tâche n'existe pas ou vous n'y avez pas accès.";
    }
    if (resource === 'team') {
      return "Cette équipe n'existe pas ou vous n'y avez pas accès.";
    }
    if (resource === 'recommendation') {
      return "Cette recommandation n'existe pas ou a été supprimée.";
    }
    return serverMessage || "La ressource demandée est introuvable ou hors de votre périmètre d'accès.";
  }

  if (status === 401) {
    return "Session expirée ou non authentifiée. Veuillez vous re-connecter.";
  }

  if (status === 400) {
    if (action === 'login') {
      return "Identifiants incorrects. Veuillez vérifier votre nom d'utilisateur et mot de passe.";
    }
    if (action === 'register') {
      return "Impossible de créer le compte. Veuillez vérifier que les informations renseignées sont valides.";
    }
    if (serverMessage && !serverMessage.toLowerCase().includes('traceback') && !serverMessage.toLowerCase().includes('exception')) {
      return serverMessage;
    }
    return "Les données soumises sont invalides. Veuillez vérifier votre saisie.";
  }

  if (status === 422) {
    return serverMessage || "Impossible de traiter la demande en raison d'une règle métier (ex: dépendance circulaire).";
  }

  if (status >= 500) {
    return "Une erreur serveur est survenue. Veuillez réessayer plus tard.";
  }

  if (err && !err.response && (err.message === 'Network Error' || err.code === 'ERR_NETWORK')) {
    return "Impossible de contacter le serveur. Veuillez vérifier votre connexion réseau.";
  }

  // Fallbacks
  if (fallback) {
    return fallback;
  }

  if (serverMessage && typeof serverMessage === 'string' && !serverMessage.toLowerCase().includes('traceback')) {
    return serverMessage;
  }

  return "Une erreur inattendue est survenue. Veuillez réessayer.";
}
