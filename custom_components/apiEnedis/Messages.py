listeMessages = \
{
    "ERR_001" : "",
    "token_refresh_401" : "Erreur de token",
    "no_data_found" : "Donnees non disponible",
    "client_not_found": "Client inconnu",
    "Invalid_request": "Erreur requete",
    "Internal Server error": "Erreur Interne",
}

def getMessage( codeMessage ):
    if ( codeMessage in listeMessages.keys()):
        return listeMessages[ codeMessage ]
    else:
        return codeMessage