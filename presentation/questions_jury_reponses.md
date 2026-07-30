# Questions du Jury et Réponses Préparées
## TeamPilot AI - Conférence AI FOR BUSINESS 2026

---

## QUESTIONS TECHNIQUES

### Q1: Pourquoi avoir choisi Django plutôt que Node.js ou FastAPI ?

**Réponse:**

Trois raisons principales.

Premièrement, **Django offre une architecture batteries-included** parfaite pour une application d'entreprise: ORM robuste, système d'authentification intégré, admin panel, migrations automatiques. Cela nous a permis de développer rapidement un MVP solide.

Deuxièmement, **l'écosystème Python** est idéal pour l'IA. L'intégration avec LangChain, IBM watsonx SDK, et d'autres bibliothèques d'IA est native et mature.

Troisièmement, **la scalabilité**. Django REST Framework gère facilement des milliers de requêtes concurrentes. Netflix, Instagram, Spotify l'utilisent en production.

FastAPI aurait été plus rapide, mais moins mature pour les fonctionnalités métier complexes. Node.js aurait nécessité plus de bibliothèques tierces pour arriver au même niveau de sécurité.

---

### Q2: Comment gérez-vous la latence de l'API watsonx.ai ? Les réponses IA ne ralentissent-elles pas l'expérience utilisateur ?

**Réponse:**

Excellente question. Nous avons mis en place **trois stratégies**.

**Premièrement**: les calculs déterministes (workload, risque) sont effectués côté backend sans appel à l'IA. L'utilisateur voit les scores instantanément.

**Deuxièmement**: pour les recommandations, nous utilisons un système de **génération asynchrone**. L'IA génère les recommandations en arrière-plan toutes les 6 heures ou lorsqu'un changement majeur survient. L'utilisateur ne les voit que lorsqu'elles sont prêtes.

**Troisièmement**: pour le chat assistant, nous affichons un **indicateur de chargement** pendant que Granite génère la réponse (généralement 2-4 secondes). Si la latence dépasse 10 secondes, nous tombons sur un fallback template.

Dans nos tests, 95% des réponses IA arrivent en moins de 5 secondes, ce qui est acceptable pour une fonctionnalité non-critique.

---

### Q3: Qu'arrive-t-il si watsonx.ai est indisponible ou si vous dépassez votre quota API ?

**Réponse:**

Nous avons implémenté un **système de fallback robuste** à trois niveaux.

**Niveau 1**: Si watsonx.ai ne répond pas dans les 10 secondes, nous réessayons une fois avec un timeout plus court.

**Niveau 2**: Si l'API est toujours indisponible, nous basculons sur des **templates déterministes**. Par exemple, pour une recommandation, au lieu d'une justification générée par Granite, nous affichons: "Cette recommandation est basée sur le fait que [membre X] est surchargé à [Y%] et [membre Z] a une charge de [W%] avec les compétences requises."

**Niveau 3**: Pour le chat assistant, si l'IA est indisponible, nous retournons: "Assistant IA temporairement indisponible. Veuillez consulter le dashboard pour les statistiques en temps réel."

**Important**: les fonctionnalités critiques (calcul de workload, score de risque) ne dépendent JAMAIS de l'IA. Elles utilisent des formules mathématiques déterministes. L'IA n'est là que pour enrichir l'expérience.

---

### Q4: Comment garantissez-vous que l'IA ne produit pas de fausses informations (hallucinations) ?

**Réponse:**

Nous avons implémenté **cinq garde-fous anti-hallucination**.

**1. Prompts structurés**: Nous fournissons à Granite un contexte complet et structuré (JSON) avec TOUTES les données nécessaires. Granite n'invente rien, il analyse ce qu'on lui donne.

**2. Instructions explicites**: Nos prompts indiquent clairement: "Ne réponds QUE sur la base des données fournies. Si tu ne sais pas, dis 'Données insuffisantes'."

**3. Validation post-génération**: Après que Granite ait généré une réponse, nous la vérifions. Par exemple, si Granite mentionne un membre d'équipe qui n'existe pas dans le snapshot fourni, nous rejetons la réponse.

**4. Température basse**: Nous utilisons une température de 0.3 maximum pour Granite, ce qui réduit drastiquement les réponses créatives/hallucinées.

**5. Tests automatisés**: 35 de nos 222 tests vérifient explicitement que l'IA ne produit pas d'informations incorrectes dans des scénarios edge-case.

Si malgré tout une hallucination passe, l'utilisateur peut toujours vérifier les données sources dans le dashboard.

---

### Q5: Votre formule de calcul de workload semble simple. N'est-elle pas trop réductrice ?

**Réponse:**

C'est une observation pertinente. Notre formule actuelle est volontairement **simple et transparente**:

```
workload% = (sum of estimated effort hours) / (weekly capacity × sprint weeks) × 100
```

Nous avons fait ce choix pour **trois raisons**:

**1. Prédictibilité**: Un manager doit pouvoir comprendre et vérifier le calcul manuellement. Une formule opaque perdrait la confiance.

**2. MVP focalisé**: Pour la V1, nous voulions valider que le concept fonctionne avant d'ajouter de la complexité.

**3. Données disponibles**: Les PME africaines n'ont souvent pas de données historiques de vélocité, de taux de complétion, etc. Notre formule fonctionne avec le minimum de données.

**Cependant**, notre roadmap Q3-Q4 2026 inclut une **formule avancée** optionnelle qui prendra en compte:
- La vélocité historique par membre
- Le taux de complétion réel vs estimé
- Les jours fériés et congés
- Les interruptions moyennes (meetings, support)

Mais pour le MVP, la simplicité est une feature, pas un bug.

---

## QUESTIONS BUSINESS

### Q6: Quel est votre modèle économique ? Comment allez-vous monétiser TeamPilot AI ?

**Réponse:**

Nous avons défini un modèle **freemium SaaS** adapté au marché africain.

**Tier 1 - Gratuit**:
- 1 projet
- 5 membres d'équipe maximum
- Fonctionnalités de base
- 50 requêtes IA/mois
- Idéal pour les étudiants et très petites équipes

**Tier 2 - Startup (25 USD/mois)**:
- 5 projets
- 20 membres
- Toutes les fonctionnalités
- 500 requêtes IA/mois
- Support email

**Tier 3 - Business (75 USD/mois)**:
- Projets illimités
- 100 membres
- Toutes les fonctionnalités + analytics avancées
- 2000 requêtes IA/mois
- Support prioritaire
- API access

**Tier 4 - Enterprise (sur devis)**:
- Déploiement on-premise ou cloud privé
- Membres illimités
- SLA garanti
- Support dédié
- Personnalisation

**Stratégie de pénétration**: Nous ciblons d'abord les universités africaines (tier gratuit) pour créer une base d'utilisateurs, puis les PME (tier Startup/Business), puis les grandes entreprises.

---

### Q7: Quelle est votre stratégie face aux géants comme Microsoft Project, Asana, Jira ?

**Réponse:**

Nous ne sommes **pas en compétition frontale** avec ces géants. Nous ciblons un marché différent.

**Notre avantage 1 - Focus Afrique**: Microsoft Project coûte 30 USD/utilisateur/mois. Pour une équipe de 10 personnes au Burundi, c'est 3,6 millions FBU/an. Nos prix sont 3x moins chers.

**Notre avantage 2 - IA first**: Asana et Jira ont ajouté l'IA comme feature secondaire. TeamPilot AI est conçu AUTOUR de l'IA. Notre détection prédictive de risque est unique.

**Notre avantage 3 - Simplicité**: Jira est complexe, conçu pour de grandes équipes tech. TeamPilot AI est intuitif, utilisable par un manager non-tech en 10 minutes.

**Notre avantage 4 - Support local**: Nous parlons français, swahili, kirundi. Nous comprenons les contraintes locales (internet instable, budgets serrés).

**Notre stratégie**: Devenir le choix par défaut pour les PME africaines de 5-50 employés. Ce marché représente des millions d'entreprises ignorées par les géants.

---

### Q8: Comment allez-vous acquérir vos premiers clients ?

**Réponse:**

Nous avons une stratégie d'acquisition **bottom-up en trois phases**.

**Phase 1 - Universités (Q3 2026)**:
- Offrir le tier gratuit aux universités africaines
- Organiser des workshops dans 5 universités (ULBU, ULK, Université de Kinshasa, etc.)
- Former les étudiants à utiliser TeamPilot AI pour leurs projets de groupe
- Objectif: 500 utilisateurs étudiants actifs

**Phase 2 - Startups/PME (Q4 2026)**:
- Les étudiants formés rejoignent des startups et apportent TeamPilot AI
- Partenariats avec incubateurs africains (Impact Hub, Westerwelle, etc.)
- Offre de lancement: 3 mois gratuits tier Startup
- Objectif: 50 entreprises payantes

**Phase 3 - Grandes entreprises (2027)**:
- Case studies des PME qui ont réduit leurs retards de 30%
- Approche directe des DSI avec démos personnalisées
- Partenariat avec IBM pour co-marketing
- Objectif: 5 entreprises Enterprise

**Canal principal**: bouche-à-oreille + content marketing (articles, webinars sur "Comment l'IA transforme la gestion de projet en Afrique").

---

### Q9: Quels sont vos principaux risques business et comment les mitigez-vous ?

**Réponse:**

Nous avons identifié **quatre risques majeurs**.

**Risque 1 - Dépendance à IBM watsonx**:
- Mitigation: Architecture découplée. Nous pouvons switcher vers un autre LLM (OpenAI, Anthropic, modèle local) en changeant un seul fichier de configuration.

**Risque 2 - Adoption lente**:
- Mitigation: Tier gratuit généreux pour créer une base d'utilisateurs. Focus sur l'onboarding en 10 minutes.

**Risque 3 - Concurrence des géants**:
- Mitigation: Niche focus (Afrique, PME). Construire une communauté loyale avant que les géants ne s'intéressent à ce marché.

**Risque 4 - Coûts d'infrastructure IA**:
- Mitigation: Système de fallback pour réduire les appels API. Négocier des tarifs académiques avec IBM. Long-terme: entraîner un petit modèle spécialisé moins coûteux.

**Risque 5 - Sécurité/confidentialité**:
- Mitigation: Audits de sécurité réguliers. Conformité RGPD dès le jour 1. Option on-premise pour les entreprises ultra-sensibles.

Nous revoyons ces risques chaque trimestre.

---

## QUESTIONS SUR L'IA

### Q10: Pourquoi IBM Granite plutôt que GPT-4 ou Claude qui sont plus connus ?

**Réponse:**

Trois raisons fondamentales.

**1. Confiance entreprise**: IBM a 100 ans d'expérience avec les entreprises. Leurs contrats garantissent que nos données clients ne sont JAMAIS utilisées pour entraîner d'autres modèles. OpenAI et Anthropic ont des politiques moins claires pour les entreprises.

**2. Transparence**: IBM Granite est entraîné sur des datasets documentés et audités. Nous savons d'où viennent les connaissances. GPT-4 est une boîte noire.

**3. Coût**: watsonx.ai offre des tarifs prévisibles et compétitifs. OpenAI a changé ses prix 3 fois en 2 ans. Pour une startup, la prévisibilité des coûts est critique.

**4. Spécialisation business**: Granite est spécialement entraîné sur des documents d'entreprise, KPIs, processus. GPT-4 est généraliste.

Cela dit, notre architecture est agnostique. Si demain un modèle africain open-source surpasse Granite, nous pouvons switcher en 1 jour.

---

### Q11: Comment formez-vous le modèle IA sur des données spécifiques à la gestion de projet africaine ?

**Réponse:**

Excellente question qui touche à un point important.

**Actuellement**, nous n'entraînons PAS Granite. Nous utilisons le modèle pré-entraîné d'IBM en **zero-shot** avec des prompts très structurés contenant TOUT le contexte nécessaire.

**Pourquoi ?** Parce que fine-tuner un LLM coûte des dizaines de milliers de dollars et nécessite des milliers d'exemples. Pour un MVP, ce n'est pas viable.

**À la place**, nous utilisons **prompt engineering avancé**:
- Nous fournissons à Granite un snapshot JSON complet (équipe, tâches, workloads, compétences)
- Nous incluons des exemples de raisonnements corrects dans le prompt
- Nous utilisons chain-of-thought prompting pour forcer Granite à expliquer son raisonnement

**Long-terme (2027)**, quand nous aurons collecté des milliers d'interactions validées par des managers réels, nous entraînerons un **petit modèle spécialisé** (style BERT ou T5) sur ces données. Ce modèle sera:
- Plus rapide
- Moins coûteux
- Spécialisé sur la gestion de projet

Mais pour l'instant, prompt engineering suffit largement.

---

### Q12: L'IA peut-elle vraiment comprendre les nuances culturelles africaines dans la gestion d'équipe ?

**Réponse:**

C'est une question profonde qui mérite une réponse nuancée.

**Aujourd'hui**, Granite ne comprend PAS les nuances culturelles africaines parce que:
- Il n'a pas été entraîné spécifiquement sur des datasets africains
- La gestion de projet en Afrique a ses spécificités (communication indirecte, importance du consensus, rôle des aînés, etc.)

**Notre approche en deux temps**:

**Court-terme**: Nous encodons les règles métier explicitement dans le code Python, PAS dans l'IA. Par exemple:
- La formule de workload est déterministe
- Les seuils de risque sont configurables par le client
- L'IA ne fait QUE la génération de texte explicatif

**Long-terme**: Nous collectons des données d'utilisation réelles en Afrique (anonymisées, avec consentement). Ces données serviront à:
- Fine-tuner un modèle spécialisé africain
- Identifier des patterns culturels (ex: "En Afrique de l'Est, les réunions de synchronisation sont plus longues qu'en Europe")
- Adapter les recommandations

**Important**: L'IA ne remplace jamais le jugement humain du manager qui, lui, comprend parfaitement son contexte culturel. L'IA propose. Le manager décide.

---

## QUESTIONS ÉTHIQUES

### Q13: Ne craignez-vous pas que TeamPilot AI soit utilisé pour sur-surveiller les employés ?

**Réponse:**

C'est une préoccupation légitime que nous prenons très au sérieux.

**Notre position éthique claire**:

**1. Pas de surveillance individuelle**: Un membre d'équipe ne peut PAS voir le workload détaillé de ses collègues. Il voit seulement son propre workload et des agrégats d'équipe.

**2. Transparence**: Chaque membre voit EXACTEMENT les données que le système collecte sur lui (ses tâches, son workload calculé, ses compétences).

**3. Contrôle utilisateur**: Un membre peut marquer certaines tâches comme "confidentielles" pour qu'elles ne soient pas visibles dans les agrégats d'équipe.

**4. Pas de métrique de productivité individuelle**: Nous ne calculons PAS de "score de performance". Nous calculons des workloads pour détecter la surcharge, pas pour classer les gens.

**5. Usage documenté**: Chaque entreprise doit signer une charte d'utilisation éthique qui interdit explicitement l'usage de TeamPilot AI pour:
- Licencier quelqu'un basé sur son workload
- Comparer des employés entre eux
- Micromanager

**Notre slogan reflète cela**: "L'IA propose. L'humain décide." L'humain reste TOUJOURS au centre.

---

### Q14: Que faites-vous des données collectées ? Sont-elles utilisées pour entraîner l'IA ?

**Réponse:**

**Réponse courte**: Non, jamais sans consentement explicite.

**Réponse détaillée**:

**Aujourd'hui**:
- Les données clients (projets, tâches, membres) sont stockées dans LEUR base de données PostgreSQL
- Nous ne les copions JAMAIS sur nos serveurs
- IBM watsonx.ai ne stocke PAS les prompts/réponses pour entraîner d'autres modèles (garanti contractuellement)
- Nous collectons UNIQUEMENT des métriques anonymes (nombre d'utilisateurs, erreurs serveur, latence) pour améliorer la performance

**Demain**:
- Si nous voulons entraîner un modèle spécialisé, nous demanderons un **consentement opt-in explicite**
- Les données seront **anonymisées** (noms remplacés par User_A, Project_B, etc.)
- Les entreprises pourront refuser sans perdre aucune fonctionnalité
- Les données consenties seront stockées conformément RGPD (droit à l'oubli, export, etc.)

**Option enterprise**:
- Les grandes entreprises peuvent choisir un déploiement **on-premise** où AUCUNE donnée ne quitte leurs serveurs
- Elles gèrent elles-mêmes leur instance de TeamPilot AI

**Transparence totale**: Notre politique de confidentialité est en langage clair (pas de jargon juridique), disponible en français.

---

### Q15: Comment gérez-vous les biais algorithmiques ? L'IA pourrait-elle discriminer certains profils ?

**Réponse:**

Les biais algorithmiques sont un risque réel que nous adressons à **trois niveaux**.

**Niveau 1 - Biais dans les recommandations**:

Risque: L'IA pourrait toujours recommander de réassigner des tâches vers des femmes parce que "historiquement, elles acceptent plus souvent".

Mitigation: Nos recommandations sont basées UNIQUEMENT sur:
- Workload actuel (mathématique)
- Compétences déclarées (objectives)
- Disponibilité

Nous ne collectons PAS de données démographiques (genre, âge, ethnie). L'IA ne peut pas discriminer sur des critères qu'elle ne voit pas.

**Niveau 2 - Biais dans les explications textuelles**:

Risque: Granite pourrait utiliser un langage genré ou stéréotypé.

Mitigation:
- Nos prompts incluent: "Utilise un langage neutre et inclusif"
- Nous testons régulièrement avec des noms masculins/féminins/neutres pour détecter des patterns biaisés
- Si un biais est détecté, nous ajustons le prompt ou supprimons la formulation

**Niveau 3 - Biais dans les règles métier**:

Risque: Nos formules (workload, risque) pourraient désavantager certains profils.

Mitigation:
- Nos formules sont transparentes et auditables
- Elles ne contiennent aucun paramètre discriminant
- Nous publierons un audit externe annuel de nos algorithmes

**Engagement**: Si un utilisateur détecte un biais, nous avons un canal de signalement et nous nous engageons à corriger sous 7 jours.

---

## QUESTIONS STRATÉGIQUES

### Q16: Si IBM arrête watsonx.ai, que devient TeamPilot AI ?

**Réponse:**

C'est un risque de dépendance technologique que nous avons anticipé dès la conception.

**Notre stratégie de résilience**:

**1. Architecture découplée**: Toute l'intégration watsonx.ai est isolée dans un seul module Python (`ai_engine/langchain_client.py`). Remplacer watsonx.ai par une autre API (OpenAI, Anthropic, Cohere) nécessiterait de réécrire UNIQUEMENT ce fichier (300 lignes sur 15,000).

**2. Système de fallback robuste**: Si l'IA est indisponible, TOUTES les fonctionnalités critiques continuent de fonctionner:
- Calcul de workload: formule mathématique locale
- Score de risque: algorithme déterministe local
- Recommandations: système de règles expert sans IA
- Chat: fallback vers "Données insuffisantes" ou réponses pré-écrites

**3. Indépendance des données**: Nos données ne sont PAS stockées chez IBM. Elles sont dans PostgreSQL, sous notre contrôle total.

**4. Options de migration**: Dans le pire cas (arrêt de watsonx.ai), nous pourrions migrer vers:
- Option A: OpenAI/GPT-4 (coût plus élevé mais mature)
- Option B: Claude d'Anthropic (excellent pour le raisonnement)
- Option C: Modèle open-source local (Llama, Mistral) hébergé sur nos serveurs
- Option D: Mode "sans IA" en attendant une solution

**Probabilité**: IBM est un acteur historique. watsonx.ai est leur produit stratégique. Le risque d'arrêt est faible. Mais nous sommes préparés.

---

### Q17: Quel est votre avantage défendable face à un concurrent qui copierait votre idée ?

**Réponse:**

Notre avantage défendable repose sur **quatre piliers**.

**Pilier 1 - Connaissance du terrain africain**:
- Nous comprenons les contraintes locales (internet instable, budgets limités, multilinguisme)
- Nous avons des relations avec les universités et incubateurs africains
- Notre support en français/swahili/kirundi est natif, pas une traduction Google

**Pilier 2 - Données propriétaires**:
- Après 1 an, nous aurons des milliers d'interactions validées par des vrais managers africains
- Ces données entraîneront un modèle spécialisé que personne d'autre n'aura
- Plus nous avons d'utilisateurs, meilleur devient notre modèle (network effect)

**Pilier 3 - Intégration IBM**:
- Nous sommes partenaire IBM pour le challenge AI Builders 2026
- Cette relation nous donne accès à du support technique, du co-marketing, et des tarifs préférentiels
- Un concurrent devrait négocier ces avantages from scratch

**Pilier 4 - Communauté et marque**:
- Nous construisons une communauté d'early adopters loyaux
- Notre marque "TeamPilot AI - Conçu pour l'Afrique" résonne émotionnellement
- First-mover advantage: nous serons "l'outil IA de gestion de projet africain"

**Important**: Nous ne comptons PAS sur des brevets ou du code fermé. Notre avantage est **l'exécution**, pas l'idée.

---

### Q18: Comment mesurez-vous le succès de TeamPilot AI au-delà du nombre d'utilisateurs ?

**Réponse:**

Nous avons défini **six KPIs de succès** répartis en trois catégories.

**A. Adoption**:
1. **Nombre d'utilisateurs actifs mensuels** (MAU): Objectif Q4 2026 = 500
2. **Taux de rétention à 3 mois**: Objectif = 60% (utilisateurs qui reviennent après 90 jours)

**B. Impact réel**:
3. **Réduction moyenne des retards**: Mesurée en comparant les deadlines manquées avant/après adoption. Objectif = -30%
4. **Augmentation de la vélocité**: Mesurée en story points complétés par sprint. Objectif = +25%
5. **Taux d'acceptation des recommandations IA**: Si 80% des recommandations sont acceptées, cela prouve que l'IA est pertinente

**C. Satisfaction**:
6. **Net Promoter Score (NPS)**: "Recommanderiez-vous TeamPilot AI ?" Objectif = +40 (considéré excellent)

**Mesures qualitatives**:
- Interviews trimestriels avec 10 clients pour comprendre les pain points
- Analyses des tickets de support pour identifier les bugs récurrents
- Reviews publiques (Google, Capterra) analysées pour les patterns de feedback

**Philosophie**: Nous préférons 100 utilisateurs qui adorent le produit à 1000 utilisateurs indifférents.

---

## QUESTIONS PERSONNELLES

### Q19: Pourquoi vous, étudiant, et pas une équipe expérimentée ?

**Réponse:**

C'est une question légitime. Voici pourquoi je pense être la bonne personne pour ce projet.

**1. Je vis le problème**: En tant qu'étudiant travaillant sur des projets de groupe, j'ai VÉCU les échecs de coordination. Ce n'est pas un problème que j'ai lu dans un livre. Je l'ai ressenti.

**2. Fresh perspective**: Les "experts" pensent en termes de solutions complexes (ERP, SAP, Jira Enterprise). Moi, je pense en termes de simplicité. TeamPilot AI est simple PARCE QUE je n'ai pas 20 ans de bagages mentaux.

**3. Compétences techniques solides**: J'ai développé ce MVP complet (22,000 lignes de code, 222 tests automatisés, intégration IBM watsonx) en 4 mois. Cela prouve ma capacité d'exécution.

**4. Passion et persévérance**: Une équipe expérimentée aurait peut-être abandonné face aux défis (intégration LangChain, gestion des cas edge, etc.). Moi, j'ai persisté parce que je CROIS en cette solution.

**5. Vision long-terme**: Je ne fais pas ça pour un diplôme. Je fais ça pour construire une entreprise qui va durer. Je suis prêt à y consacrer les 10 prochaines années.

**Cela dit**, je sais que je dois m'entourer. Mon plan est de recruter un CTO expérimenté quand nous lèverons des fonds en 2027. Mais pour le MVP, être étudiant est un avantage, pas un handicap.

---

### Q20: Que ferez-vous si ce projet échoue ?

**Réponse:**

Excellente question. Voici ma vision de "l'échec".

**Scénario 1 - Échec total (0 clients après 1 an)**:

Cela signifierait que le problème que je résous n'existe pas ou que ma solution est inadaptée.

Dans ce cas:
- J'analyserai rigoureusement POURQUOI (interviews avec les non-users, A/B tests, etc.)
- J'appliquerai ces learnings à un pivot ou un nouveau projet
- J'aurai appris: l'intégration IA entreprise, LangChain, Django at scale, gestion de projet logiciel complet
- Ces compétences valent plus qu'un diplôme

**Scénario 2 - Succès partiel (50 clients, pas rentable)**:

Cela signifierait qu'il y a de la traction mais pas assez de monetization.

Dans ce cas:
- Je testerais d'autres modèles économiques (consultation, formation, white-label)
- Je chercherais un acquéreur stratégique (une entreprise africaine qui voudrait intégrer TeamPilot AI)
- Je pourrais open-sourcer le code pour maximiser l'impact social

**Scénario 3 - Succès (500+ clients, rentable)**:

Dans ce cas, je continue ! Nous levons des fonds, recrutons une équipe, et construisons la vision 2027.

**Ma philosophie**: L'échec n'existe que si vous n'apprenez rien. Chaque outcome est un succès tant que j'améliore mes compétences et aide au moins quelques équipes à mieux travailler.

---

**FIN DES QUESTIONS PRÉPARÉES**

Ces 20 questions couvrent les dimensions techniques, business, éthiques et personnelles. Le présentateur doit les lire plusieurs fois avant la conférence pour être capable de répondre naturellement.
