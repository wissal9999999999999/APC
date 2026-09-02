# Diagramme de séquence — génération et alignement des AAD

```mermaid
sequenceDiagram
    autonumber
    actor RF as Responsable de formation
    actor REC as Responsable d'EC
    participant UI as Application Angular
    participant API as API Flask
    participant GEN as Agent générateur d'AAD
    participant ALIGN as Moteur d'alignement
    participant DATA as BDD / fichiers JSON

    rect rgb(255, 247, 179)
        Note over RF,DATA: Phase 1 — Constitution du référentiel de formation
        RF->>UI: Saisir un apprentissage critique (AC)
        UI->>API: POST /api/ac
        API->>DATA: Enregistrer l'AC et mettre à jour ac_{formation}.json
        DATA-->>API: AC enregistré
        API-->>UI: Identifiant et confirmation
        UI-->>RF: AC disponible dans le référentiel
    end

    rect rgb(225, 239, 255)
        Note over REC,DATA: Phase 2 — Identification des AAD à partir des cours
        REC->>UI: Déposer un ou plusieurs cours PDF
        UI->>API: POST /api/identify (PDF, matière)
        API->>GEN: Lancer generation_worker
        GEN->>GEN: Extraire et agréger le texte des PDF
        GEN->>GEN: Générer les AAD avec l'agent IA
        GEN-->>API: Liste structurée des AAD
        API->>DATA: Écrire aad_{matière}.json
        API-->>UI: AAD générés
        UI-->>REC: Afficher les formulations proposées

        REC->>UI: Sélectionner les AAD pertinents
        UI->>API: POST /api/aad/{matière}/selection
        API->>DATA: Écrire aad_selection_{matière}.json
        API-->>UI: Sélection enregistrée
        UI-->>REC: Confirmation et téléchargement JSON
    end

    rect rgb(226, 247, 226)
        Note over REC,DATA: Phase 3 — Alignement sémantique AAD–AC
        REC->>UI: Fournir les AAD et lancer l'alignement
        UI->>API: POST /api/align/json
        API->>DATA: Charger les AC de la formation
        DATA-->>API: Catalogue des AC
        API->>ALIGN: Lancer alignment_worker (AAD, AC, seuil)
        ALIGN->>ALIGN: Encoder avec Sentence-CamemBERT
        ALIGN->>ALIGN: Calculer et classer les similarités cosinus
        ALIGN-->>API: AC candidats, scores et meilleur résultat
        API->>DATA: Écrire alignment_{matière}.json
        API-->>UI: Résultats d'alignement
        UI-->>REC: Afficher le meilleur AC et les correspondances
        REC->>UI: Télécharger le résultat
        UI->>API: GET /api/align/{matière}/download
        API->>DATA: Lire le fichier d'alignement
        DATA-->>API: JSON final
        API-->>REC: Télécharger alignment_{matière}.json
    end
```

**Figure — Flux centralisé de génération et d'alignement des acquis d'apprentissage disciplinaires (AAD) avec les apprentissages critiques (AC).**

