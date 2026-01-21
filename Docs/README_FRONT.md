# 🎨 Frontend - CV Extract Pro - Sopra Steria

Interface moderne et réactive pour l'analyse et la génération automatique de CV développée avec **React 19**, **Vite** et **Tailwind CSS**.

L'application propose une expérience utilisateur intuitive permettant d'uploader des CV (PDF/DOCX), d'extraire automatiquement les informations et de générer des documents standardisés au format Sopra Steria.

---

## 🚀 Stack Technique

| Technologie | Version | Rôle |
|-------------|---------|------|
| **React** | 19.2.0 | Composants UI modernes et réactifs |
| **Vite** | 7.1.8 | Bundler ultra-rapide avec HMR |
| **Tailwind CSS** | 4.1.14 | Styling responsive et personnalisable |
| **React Router DOM** | 7.9.3 | Navigation multi-pages |
| **Lucide React** | 0.544.0 | Icônes vectorielles modernes |
| **Chart.js** | 4.5.1 | Visualisation données (graphiques) |
| **ESLint** | 9.36.0 | Linting et qualité de code |

---

## 📁 Structure du Projet

```
frontend/
│
├── src/
│   ├── components/               # 🧩 Composants réutilisables
│   │   ├── Navbar.jsx            # Barre de navigation + dark mode
│   │   ├── HeroSection.jsx       # Section hero avec CTA
│   │   └── SopraLogo.jsx         # Logo Sopra Steria
│   │
│   ├── pages/                    # 📄 Pages principales
│   │   ├── Home/
│   │   │   ├── Home.jsx
│   │   │   └── Home.css
│   │   ├── HowItWorks/           # Page fonctionnement
│   │   ├── Start/                # Page démarrage
│   │   ├── Normalize/            # Page normalisation
│   │   └── Example/              # Page exemples
│   │
│   ├── hooks/                    # 🪝 Custom Hooks React
│   │   └── useDarkMode.js        # Gestion du thème clair/sombre
│   │
│   ├── assets/                   # 🖼️ Ressources
│   │   ├── hero-cv.png
│   │   ├── react.svg
│   │   ├── images/               # Screenshots et previews
│   │   │   ├── preview1.png
│   │   │   ├── preview2.png
│   │   │   ├── preview3.png
│   │   │   └── preview4.png
│   │   └── logos/
│   │       ├── logo2.png
│   │       └── sopra-steria-logo.svg
│   │
│   ├── utils/                    # 🔧 Utilitaires
│   │   └── constants.js          # Constantes (couleurs, API URLs, etc)
│   │
│   ├── styles/                   # 🎨 Styles globaux
│   │   └── index.css             # Variables CSS, reset, thème global
│   │
│   ├── App.jsx                   # 🗺️ Routing et structure app
│   ├── main.jsx                  # 🔌 Point d'entrée React
│   └── index.html               # Point d'entrée HTML
│
├── public/                       # 📊 Fichiers statiques
│   ├── logo.png
│   └── vite.svg
│
├── images/                       # 🖼️ Images du projet
│   ├── preview1.png
│   ├── preview2.png
│   ├── preview3.png
│   └── preview4.png
│
├── tailwind.config.js            # ⚙️ Configuration Tailwind
├── postcss.config.cjs            # PostCSS config (AutoPrefixer)
├── vite.config.js                # ⚙️ Configuration Vite
├── eslint.config.js              # 🔍 Règles ESLint
├── package.json                  # 📦 Dépendances
├── index.html                    # 🌐 HTML principal
└── README.md                     # Ce fichier
```

---

## 🎨 Design & Thème

### Palette de couleurs

| Élément | Valeur | Utilisation |
|---------|--------|-------------|
| **Primaire** | rgb(221, 83, 52) / #DD5334 | Boutons, accents, hover |
| **Gradient** | linear-gradient(90deg, #880015, #FF5614) | Titres, bannières |
| **Fond clair** | #FFFFFF / #F8F9FA | Mode clair |
| **Fond sombre** | #1A1A1A / #2A2A2A | Mode sombre |
| **Texte clair** | #000000 / #1F2937 | Texte mode clair |
| **Texte sombre** | #FFFFFF / #F0F0F0 | Texte mode sombre |

### Polices

- **Raleway** : Police générale (body text)
- **Manrope** : Titres et chiffres (statistiques)

### Modes

- 🌞 **Mode Clair** : Interface lumineuse et épurée
- 🌙 **Mode Sombre** : Interface sombre pour réduction fatigue oculaire
- 💾 **Persistance** : Le choix du mode est sauvegardé dans localStorage

---

## ⚙️ Installation & Configuration

### 1. Cloner le projet

```bash
git clone https://github.com/DorianLn/Projet-Sopra-Steria.git
cd Projet-Sopra-Steria/frontend
```

### 2. Installer les dépendances

```bash
npm install
```

### 3. Lancer le serveur de développement

```bash
npm run dev
```

✅ L'application sera disponible sur **http://localhost:5173**

### 4. Build pour la production

```bash
npm run build
```

### 5. Prévisualiser le build

```bash
npm run preview
```

### 6. Linter et vérifier la qualité

```bash
npm run lint
```

---

## 📦 Scripts disponibles

| Commande | Description |
|----------|-------------|
| `npm run dev` | Lancer serveur développement (Vite) avec HMR |
| `npm run build` | Construire pour production (dist/) |
| `npm run preview` | Prévisualiser le build production localement |
| `npm run lint` | Vérifier la qualité du code avec ESLint |

---

## 🎯 Fonctionnalités principales

### 1. 📤 Upload de CV

- Support **PDF** et **DOCX**
- Drag & drop
- Validation taille fichier
- Feedback utilisateur

### 2. 🔍 Affichage résultats

- Données extraites formatées
- Prévisualisation JSON
- Export des résultats

### 3. 🌗 Mode Clair/Sombre

- Toggle dans la Navbar
- Persistance avec localStorage
- Transitions fluides

### 4. 📱 Design Responsive

- Mobile First
- Optimisé pour desktop, tablet, mobile
- Navigation fluide sur tous appareils

### 5. 📊 Statistiques & Visualisations

- Graphiques avec Chart.js
- Données analyse CV
- Performance extraction

---

## 🔗 Intégration Backend

L'application communique avec le backend Flask via une API REST.

### Configuration API

Éditer le fichier `src/utils/constants.js` :

```javascript
export const API_BASE_URL = 'http://localhost:5000';
export const API_ENDPOINTS = {
  ANALYZE_CV: '/api/cv/analyze',
  DOWNLOAD_DOCX: '/api/cv/docx/',
  DOWNLOAD_PDF: '/api/cv/pdf/'
};
```

### Exemple d'appel API

```javascript
const uploadCV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await fetch(`${API_BASE_URL}/api/cv/analyze`, {
    method: 'POST',
    body: formData
  });
  
  return await response.json();
};
```

---

## 🎨 Composants principaux

### Navbar.jsx
Barre de navigation sticky avec :
- Logo Sopra Steria
- Menu de navigation
- Toggle Dark Mode
- Responsive menu mobile

### HeroSection.jsx
Section d'accueil avec :
- Titre et sous-titre
- Call-to-action (boutons)
- Statistiques clés
- Image hero

### SopraLogo.jsx
Logo branding Sopra Steria intégré

---

## 🧪 Tests

```bash
# Lancer ESLint
npm run lint

# Corriger les erreurs ESLint automatiquement
npm run lint -- --fix
```

---

## 🚀 Déploiement

### Préparation

```bash
npm run build
```

Cela génère le dossier `dist/` avec les fichiers optimisés.

### Sur un serveur

```bash
# Copier le contenu de dist/ sur votre serveur
# Configuration nginx exemple:
server {
    listen 80;
    server_name votre-domaine.com;
    root /var/www/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

---

## 🔧 Améliorations futures

- [ ] Optimisation du Dark Mode (meilleurs contrastes)
- [ ] Animations transitions (Framer Motion)
- [ ] PWA (Progressive Web App)
- [ ] Multilingue (i18n)
- [ ] Authentification utilisateur
- [ ] Historique analyses
- [ ] Partage résultats
- [ ] Export Excel/CSV

---

## 👥 Contributeurs

- 👩‍💻 Safae Berrichi
- 👨‍💻 Nehade El Mokhtari
- 👨‍💻 Clément
- 👨‍💻 Julien Thepaut
- 👨‍💻 Dorian Lo Negro
- 👨‍💻 Thomas Gaugeais

---

## 📜 Licence

Projet réalisé dans le cadre d'un partenariat pédagogique avec **Sopra Steria**.  
Tous droits réservés.

---

## 🌐 Ressources

- [Vite Documentation](https://vitejs.dev/)
- [React Documentation](https://react.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [React Router](https://reactrouter.com/)
- [ESLint](https://eslint.org/)
