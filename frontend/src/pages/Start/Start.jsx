import React, { useState } from "react";
import Navbar from "../../components/Navbar";
import SopraLogo from "../../components/SopraLogo";
import {
  Upload,
  FileText,
  ArrowRight,
  Download,
  BarChart3,
  FileDown,
  Eye,
} from "lucide-react";
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from "chart.js";
import { Radar } from "react-chartjs-2";
import "./Start.css";

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

// ---- Helpers ----
const computeExtractionScore = (result) => {
  if (!result) return 0;
  let score = 0;

  // === POINTS DE BASE (tout doit être présent) ===
  const hasNom = result.contact?.nom ? 1 : 0;
  const hasEmail = result.contact?.email ? 1 : 0;
  const hasFormations = Array.isArray(result.formations) && result.formations.length > 0 ? 1 : 0;
  const hasExperiences = result.experiences ? 1 : 0;
  const hasCompetences =
    (Array.isArray(result.competences?.techniques) && result.competences.techniques.length > 0) ||
    (Array.isArray(result.competences?.fonctionnelles) && result.competences.fonctionnelles.length > 0) ? 1 : 0;
  const hasLangues = Array.isArray(result.langues) && result.langues.length > 0 ? 1 : 0;

  // Score de structure : avoir tous les éléments clés (max 75%)
  score += hasNom * 12;        // Nom obligatoire
  score += hasEmail * 8;       // Email bonus
  score += hasFormations * 12; // Formations
  score += hasExperiences * 15; // Expériences
  score += hasCompetences * 12; // Compétences
  score += hasLangues * 8;     // Langues

  // === POINTS DE RICHESSE (completude) - max 20% ===
  // Plus il y a de formations, mieux c'est
  if (hasFormations) {
    const formCount = Math.min(result.formations.length, 5);
    score += formCount * 1.5; // 0 à 7.5 points
  }

  // Plus il y a d'expériences, mieux c'est
  if (hasExperiences) {
    let expCount = 0;
    if (typeof result.experiences === "string") {
      expCount = result.experiences.trim().length > 100 ? 3 : 1;
    } else if (Array.isArray(result.experiences)) {
      expCount = Math.min(result.experiences.length, 6);
    }
    score += expCount * 1.2; // 0 à 7.2 points
  }

  // Plus il y a de compétences, mieux c'est
  const compCount =
    (result.competences?.techniques?.length || 0) +
    (result.competences?.fonctionnelles?.length || 0);
  if (compCount > 0) {
    const capped = Math.min(compCount, 10);
    score += capped * 0.8; // 0 à 8 points
  }

  // === PENALTIES ===
  let penalties = 0;

  // Nom mal extrait (contient un métier)
  if (result.contact?.nom && /développeur|ingénieur|chef|manager|architecte|consultant/i.test(result.contact.nom)) {
    penalties += 5;
  }

  score -= penalties;
  return Math.max(0, Math.min(95, score)); // MAX 95%
};

const computeProfessionalCvScore = (result) => {
  if (!result) return 0;
  let score = 0;

  // 1) Richesse compétences - AUGMENTÉ
  const comp = [
    ...(result.competences?.techniques || []),
    ...(result.competences?.fonctionnelles || []),
  ];

  const compText = comp.join(" ").toLowerCase();
  const hasBackend = /python|java|spring|node|django|c\+\+|rust|golang/i.test(compText);
  const hasFrontend = /react|angular|vue|html|css|javascript|typescript/i.test(compText);
  const hasCloud = /aws|azure|gcp|cloud|docker|kubernetes|ci\/cd|devops/i.test(compText);
  const hasSoft = /communication|leadership|gestion|management|agile|scrum|safe/i.test(compText);
  const hasDatabase = /sql|postgres|mysql|mongodb|elasticsearch|oracle/i.test(compText);

  score += (hasBackend + hasFrontend + hasCloud + hasSoft + hasDatabase) * 5; // max 25

  // 2) Expérience totale - AUGMENTÉ
  const years = estimateExperienceLevel(result).years;
  if (years >= 7) score += 25;
  else if (years >= 4) score += 18;
  else if (years >= 2) score += 12;
  else if (years >= 1) score += 6;

  // 3) Études - AUGMENTÉ & BONUS CERTIFICATIONS
  const formations = result.formations || [];
  const formText = formations.join(" ").toLowerCase();

  let formScore = 0;
  if (/master|bac\+5|ingénieur|grande école/i.test(formText)) {
    formScore = 15;
  } else if (/licence|bac\+3/i.test(formText)) {
    formScore = 10;
  } else if (formations.length > 0) {
    formScore = 5;
  }

  // Bonus certifications professionnelles
  if (/istqb|psm|safe|scrum|aws|azure/i.test(formText)) {
    formScore += 8;
  }

  score += formScore;

  // 4) Richesse des compétences (nombre) - AUGMENTÉ
  if (comp.length >= 15) score += 12;
  else if (comp.length >= 10) score += 10;
  else if (comp.length >= 6) score += 7;
  else if (comp.length >= 3) score += 4;

  // 5) Langues
  const langues = result.langues || [];
  if (langues.length >= 2) score += 10;
  else if (langues.length === 1) score += 5;

  // 6) Structure et complétude
  const hasContact = result.contact?.nom ? 1 : 0;
  const hasFormations = formations?.length > 0 ? 1 : 0;
  const hasExperiences = result.experiences ? 1 : 0;
  const hasSkills = comp.length > 0 ? 1 : 0;
  const hasLangues = langues.length > 0 ? 1 : 0;

  const structureSections = hasContact + hasFormations + hasExperiences + hasSkills + hasLangues;
  score += structureSections * 3; // max 15

  // 7) BONUS : Nombre d'expériences nombreuses
  if (Array.isArray(result.experiences) && result.experiences.length >= 5) {
    score += 5;
  }

  return Math.min(100, score);
};

const estimateExperienceLevel = (result) => {
  if (!result?.experiences) return { label: "Non déterminé", years: 0 };

  let minYear = 9999;
  let maxYear = 0;

  const extractYear = (str) => {
    if (!str) return null;
    // Chercher une plage : "2020-2023" ou "2020 à 2023"
    const range = str.match(/(19|20)\d{2}\s*[-–à]\s*(19|20)\d{2}/);
    if (range) {
      const years = str.match(/(19|20)\d{2}/g);
      if (years && years.length >= 2) {
        return { start: parseInt(years[0], 10), end: parseInt(years[1], 10) };
      }
    }
    // Chercher une seule année
    const single = str.match(/(19|20)\d{2}/);
    if (single) {
      const y = parseInt(single[0], 10);
      return { start: y, end: y };
    }
    return null;
  };

  // Traiter experiences (peut être string ou array)
  if (typeof result.experiences === "string") {
    const parsed = extractYear(result.experiences);
    if (parsed) {
      minYear = Math.min(minYear, parsed.start);
      maxYear = Math.max(maxYear, parsed.end);
    }
  } else if (Array.isArray(result.experiences)) {
    result.experiences.forEach((exp) => {
      const expStr = typeof exp === "string" ? exp : (exp.title || "");
      const parsed = extractYear(expStr);
      if (parsed) {
        minYear = Math.min(minYear, parsed.start);
        maxYear = Math.max(maxYear, parsed.end);
      }
    });
  }

  if (minYear === 9999 || maxYear === 0) {
    return { label: "Non déterminé", years: 0 };
  }

  const years = Math.max(0, maxYear - minYear + 1);

  let label = "Junior";
  if (years >= 5) label = "Senior";
  else if (years >= 2) label = "Intermédiaire";

  return { label, years };
};

const buildRadarData = (result) => {
  if (!result?.competences?.techniques) {
    return {
      labels: ["Compétences"],
      datasets: [
        {
          label: "Compétences",
          data: [1],
        },
      ],
    };
  }

  // Étape 1 : extraire les vraies compétences unitaires
  let extractedSkills = [];

  result.competences.techniques.forEach((bloc) => {
    // On sépare au niveau du ":" si présent
    const parts = bloc.split(":");

    if (parts.length > 1) {
      // On prend la partie après le :
      const skillsPart = parts[1];

      // On sépare par virgules
      const skills = skillsPart.split(",");

      skills.forEach((s) => {
        const clean = s.trim();

        if (clean.length > 1) {
          extractedSkills.push(clean);
        }
      });
    } else {
      // Si pas de ":", on garde la ligne brute
      extractedSkills.push(bloc.trim());
    }
  });

  // Supprimer doublons
  extractedSkills = [...new Set(extractedSkills)];

  // Limiter à 7 compétences max pour lisibilité radar
  extractedSkills = extractedSkills.slice(0, 7);

  if (!extractedSkills.length) {
    return {
      labels: ["Compétences"],
      datasets: [
        {
          label: "Compétences",
          data: [1],
        },
      ],
    };
  }

  // Valeurs arbitraires pour affichage
  const values = extractedSkills.map(() => 3);

  return {
    labels: extractedSkills,
    datasets: [
      {
        label: "Compétences clés",
        data: values,
        backgroundColor: "rgba(255, 88, 120, 0.2)",
        borderColor: "rgba(214, 46, 92, 0.9)",
        borderWidth: 2,
        pointRadius: 3,
      },
    ],
  };
};

const exportPdf = () => {
  // version simple : impression de la page (l’utilisateur peut choisir "Enregistrer en PDF")
  window.print();
};

const formatExperience = (text) => {
  if (!text) return { line1: text, line2: "" };

  // Extraire la date
  const dateMatch = text.match(
    /(19|20)\d{2}\s?[–-]\s?(19|20)\d{2}|(19|20)\d{2}/
  );

  if (!dateMatch) {
    return { line1: text, line2: "" };
  }

  const date = dateMatch[0];

  // Retirer la date du texte
  let rest = text.replace(date, "").trim();

  // Supprimer éventuel préfixe S1 S2 S3...
  rest = rest.replace(/^S\d\s*/, "").trim();

  // On coupe la description à partir de mots clés typiques
  const keywords = ["Programme", "Stage", "Projet", "Formation"];

  let index = -1;

  for (let key of keywords) {
    index = rest.indexOf(key);
    if (index !== -1) break;
  }

  let title = rest;
  let description = "";

  // --- AJOUT MINIMAL : gestion des multiples "Projet individuel" (cas Léo) ---
  if (rest.includes("Projet individuel")) {
    const parts = rest
      .split("Projet individuel")
      .map((p) => p.trim())
      .filter((p) => p);

    const mainTitle = parts.shift();

    return {
      line1: `${date} ${mainTitle} : Projets`,
      line2: parts.map((p) => "Projet individuel " + p).join("\n"),
    };
  }

  if (index !== -1) {
    title = rest.substring(0, index).trim();
    description = rest.substring(index).trim();
  }

  return {
    line1: `${date}  ${title}`,
    line2: description,
  };
};

const formatFormationSimple = (input) => {
  // Si déjà un objet (cas JLA normalisé)
  if (typeof input === "object" && input !== null) {
    return {
      title: input.title || "",
      description: input.year ? `(${input.year})` : "",
    };
  }

  // Cas Léo : string classique
  if (typeof input !== "string") {
    return { title: "", description: "" };
  }

  if (!input.includes(":")) {
    return { title: input, description: "" };
  }

  const [title, ...rest] = input.split(":");

  return {
    title: title.trim(),
    description: rest.join(":").trim(),
  };
};

const formatBoldBeforeColon = (input) => {
  if (typeof input === "object" && input !== null) {
    return {
      title: input.title || "",
      description: input.description || "",
    };
  }

  if (typeof input !== "string") {
    return { title: "", description: "" };
  }

  if (!input.includes(":")) {
    return { title: input, description: "" };
  }

  const [title, ...rest] = input.split(":");

  return {
    title: title.trim(),
    description: rest.join(":").trim(),
  };
};

const normalizeCvData = (data) => {
  if (!data) return data;

  // On crée une copie pour ne pas modifier l’original
  let result = JSON.parse(JSON.stringify(data));

  // ========== DETECTION TYPE JLA ==========
  const isJla =
    Array.isArray(result.experiences) &&
    result.experiences.some(
      (line) => typeof line === "string" && !/(19|20)\d{2}/.test(line)
    );

  if (!isJla) {
    // CAS LEO → on ne touche à rien
    return result;
  }

  // ========================
  // CAS JLA : NORMALISATION
  // ========================

  // ---- 1) EXPERIENCES ----
  let grouped = [];
  let current = null;

  const actionVerbs = [
    "Réponses",
    "Assurer",
    "Développer",
    "Procéduriser",
    "Rédaction",
    "Accompagner",
    "Mettre en place",
    "Suivi",
    "Participation",
    "Réalisation",
  ];

  result.experiences.forEach((line) => {
    const isTitle = /(19|20)\d{2}/.test(line);

    if (isTitle) {
      if (current) grouped.push(current);

      let title = line;
      let firstBullet = null;

      // Détection d'un verbe d’action collé au titre
      for (let verb of actionVerbs) {
        const index = line.indexOf(" " + verb + " ");
        if (index !== -1) {
          title = line.substring(0, index).trim();
          firstBullet = line.substring(index + 1).trim();
          break;
        }
      }

      current = {
        title: title,
        bullets: firstBullet ? [firstBullet] : [],
      };
    } else if (current) {
      current.bullets.push(line);
    }
  });

  if (current) grouped.push(current);

  result.experiences = grouped;

  // ---- 2) FORMATIONS ----
  if (Array.isArray(result.formations)) {
    result.formations = result.formations.map((f) => {
      if (typeof f !== "string") return f;

      const match = f.match(/^((19|20)\d{2})\s*[-–]?\s*(.*)$/);

      if (match) {
        return {
          title: match[3],
          year: match[1],
        };
      }

      return {
        title: f,
        year: "",
      };
    });
  }

  // ---- 3) COMPETENCES FONCTIONNELLES ----
  if (Array.isArray(result.competences?.fonctionnelles)) {
    result.competences.fonctionnelles = result.competences.fonctionnelles.map(
      (c) => {
        if (!c.includes(":")) {
          return { title: c, description: "" };
        }

        const [title, ...rest] = c.split(":");

        return {
          title: title.trim(),
          description: rest.join(":").trim(),
        };
      }
    );
  }

  return result;
};

const Start = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [modifiedDocx, setModifiedDocx] = useState(null);
  const [generatedDocxName, setGeneratedDocxName] = useState(null);


  // --- Conversion DOCX modifié en PDF ---
  const convertDocxToPdf = async () => {
    try {
      // CAS 1 : DOCX modifié importé
      if (modifiedDocx) {
        const formData = new FormData();
        formData.append("file", modifiedDocx);

        const response = await fetch("http://localhost:5000/api/cv/convert", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const err = await response.json();
          throw new Error(err.error || "Erreur lors de la conversion");
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = "CV_Modifié.pdf";
        a.click();

        URL.revokeObjectURL(url);
        return;
      }

      // CAS 2 : conversion directe du DOCX généré
      if (!generatedDocxName) {
        alert("Veuillez d'abord télécharger le DOCX avant de le convertir.");
        return;
      }

      const response = await fetch("http://localhost:5000/api/cv/convert", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          filename: generatedDocxName,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || "Erreur lors de la conversion");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);

      const a = document.createElement("a");
      a.href = url;
      a.download = `${generatedDocxName}.pdf`;
      a.click();

      URL.revokeObjectURL(url);

    } catch (e) {
      alert("Erreur : " + e.message);
    }
  };


  // --- Gestion du drag & drop ---
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    const file = e.dataTransfer.files[0];
    handleFileSelect({ target: { files: [file] } });
  };

  // --- Sélection du fichier ---
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && (file.name.endsWith(".docx") || file.name.endsWith(".pdf"))) {
      setSelectedFile(file);
      setError(null);
      setResult(null);
    } else {
      alert("Veuillez sélectionner un fichier .docx ou .pdf");
    }
  };

  // --- Soumission vers le backend ---
  const handleSubmit = async () => {
    if (!selectedFile) return alert("Veuillez sélectionner un fichier");

    const formData = new FormData();
    formData.append("file", selectedFile);

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:5000/api/cv/analyze", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      if (!response.ok)
        throw new Error(data.error || "Erreur lors de l’analyse");

      setResult(normalizeCvData(data));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const extractionScore = Math.round(computeExtractionScore(result));
  const professionalScore = Math.round(computeProfessionalCvScore(result));
  const xpInfo = estimateExperienceLevel(result);
  const radarData = buildRadarData(result);

  return (
    <div className="start-page">
      <Navbar />
      <main className="start-section">
        <div className="start-container text-center max-w-5xl mx-auto">
          <SopraLogo className="hero-logo" />
          <h1 className="hero-title">
            Analysez votre <span className="gradient-text">CV</span>
          </h1>
          <p className="hero-subtitle">
            Téléversez votre CV (.docx ou .pdf) pour une extraction automatique
            des informations clés.
          </p>

          {/* Zone de téléchargement */}
          <div className="mt-10 relative">
            <div
              className={`upload-zone ${dragActive ? "drag-active" : ""}`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <input
                type="file"
                accept=".docx,.pdf"
                onChange={handleFileSelect}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="upload-content">
                <Upload className="upload-icon" />
                {selectedFile ? (
                  <div className="space-y-2">
                    <div className="file-selected">
                      <FileText className="file-selected-icon" />
                      <span className="file-selected-name">
                        {selectedFile.name}
                      </span>
                    </div>
                    <p className="file-ready">Fichier prêt à être analysé</p>
                  </div>
                ) : (
                  <>
                    <h3 className="upload-title">
                      Glissez-déposez votre CV ici
                    </h3>
                    <p className="upload-description">
                      ou cliquez pour sélectionner un fichier
                    </p>
                    <p className="upload-format">
                      Formats acceptés : .docx, .pdf
                    </p>
                  </>
                )}
              </div>
            </div>

            {/* Bouton de traitement */}
            {selectedFile && (
              <div className="submit-section">
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="submit-button"
                >
                  {loading ? "Analyse en cours..." : "Analyser le CV"}
                  <ArrowRight />
                </button>
              </div>
            )}
          </div>

          {/* Gestion des erreurs */}
          {error && (
            <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md text-red-700">
              {error}
            </div>
          )}

          {/* Résultat affiché */}
          {result && (
            <div className="result-section text-left mt-10">
              {/* Barre d’outils / résumé */}
              <div className="result-toolbar">
                {/* Score extraction */}
                <div className="score-block">
                  <span className="score-label">Fiabilité extraction</span>
                  <div className="score-value">
                    <BarChart3 size={18} />
                    <span>{extractionScore}%</span>
                  </div>
                  <div className="score-bar">
                    <div
                      className="score-bar-fill"
                      style={{ width: `${extractionScore}%` }}
                    />
                  </div>

                  {/* Score Pro */}
                  <div className="score-block">
                    <span className="score-label">Score CV Pro</span>
                    <div className="score-value">
                      <BarChart3 size={18} />
                      <span>{professionalScore}%</span>
                    </div>
                    <div className="score-bar">
                      <div
                        className="score-bar-fill"
                        style={{ width: `${professionalScore}%` }}
                      />
                    </div>
                  </div>
                </div>

                {/* XP */}
                <div className="xp-block">
                  <span className="xp-label">Niveau d’expérience</span>
                  <span className="xp-pill">
                    {xpInfo.label}{" "}
                    {xpInfo.years > 0 && `(${xpInfo.years} ans estimés)`}
                  </span>
                </div>

                <div className="export-buttons">
                  <button
                    className="export-btn"
                    onClick={() => {
                      if (!result?.json_filename) {
                        alert("Aucun JSON disponible.");
                        return;
                      }

                      window.open(
                        `http://localhost:5000/api/cv/json/${result.json_filename.replace(
                          ".json",
                          ""
                        )}`,
                        "_blank"
                      );
                    }}
                  >
                    <Download size={16} />
                    JSON
                  </button>
                  <button
                    className="export-btn"
                    onClick={() => {
                      if (!result?.json_filename) {
                        alert("Aucun JSON trouvé pour générer le Word.");
                        return;
                      }

                      const baseName = result.json_filename.replace(
                        ".json",
                        ""
                      );

                      // Mémoriser le nom du DOCX généré
                      setGeneratedDocxName(baseName);

                      window.open(
                        `http://localhost:5000/api/cv/docx/${baseName}`,
                        "_blank"
                      );
                    }}
                  >
                    <FileText size={16} />
                    DOCX
                  </button>
                  {/* Sélection du CV Word modifié */}
                  <input
                    type="file"
                    accept=".docx"
                    style={{ display: "none" }}
                    id="upload-modified-docx"
                    onChange={(e) => setModifiedDocx(e.target.files[0])}
                  />

                  <label htmlFor="upload-modified-docx" className="export-btn">
                    <Upload size={16} />
                    Importer DOCX modifié
                  </label>

                  {/* Convertir en PDF */}
                  <button
                    className="export-btn"
                    onClick={convertDocxToPdf}
                    disabled={false}
                  >
                    <FileDown size={16} />
                    Convertir en PDF
                  </button>
                </div>
              </div>

              {/* Grille principale */}
              <div className="result-wrapper">
                {/* CONTACT */}
                <div className="result-card">
                  <h3 className="result-title">📞 Contact</h3>
                  <ul className="result-list text-gray-700">
                    {result.contact.nom && (
                      <li>
                        <strong>Nom :</strong> {result.contact.nom}
                      </li>
                    )}
                    {result.contact.email && (
                      <li>
                        <strong>Email :</strong> {result.contact.email}
                      </li>
                    )}
                    {result.contact.telephone && (
                      <li>
                        <strong>Téléphone :</strong> {result.contact.telephone}
                      </li>
                    )}
                    {result.contact.adresse && (
                      <li>
                        <strong>Adresse :</strong> {result.contact.adresse}
                      </li>
                    )}
                  </ul>
                </div>

                {/* FORMATIONS */}
                {result.formations?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">
                      🎓 Formations - Certification{" "}
                    </h3>
                    <ul className="result-list text-gray-700">
                      {result.formations.map((f, i) => {
                        const form = formatFormationSimple(f);

                        return (
                          <li key={i} className="mb-2">
                            <strong>{form.title}</strong> : {form.description}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}

                {/* EXPERIENCES */}
                {result.experiences?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">💼 Expériences</h3>
                    <ul className="result-list text-gray-700">
                      {result.experiences.map((exp, i) => (
                        <li key={i} className="mb-3">
                          {typeof exp === "string" ? (
                            // CAS LEO (inchangé)
                            (() => {
                              const e = formatExperience(exp);
                              return (
                                <>
                                  <strong>{e.line1}</strong>
                                  {e.line2 && (
                                    <div>
                                      {e.line2.split("\n").map((l, idx) => (
                                        <div key={idx}>{l}</div>
                                      ))}
                                    </div>
                                  )}{" "}
                                </>
                              );
                            })()
                          ) : (
                            // CAS JLA (déjà normalisé)
                            <>
                              <strong>{exp.title}</strong>

                              {exp.bullets?.length > 0 && (
                                <ul className="ml-4 mt-1 list-disc">
                                  {exp.bullets.map((b, j) => (
                                    <li key={j}>{b}</li>
                                  ))}
                                </ul>
                              )}
                            </>
                          )}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* COMPETENCES TECHNIQUES */}
                {result.competences?.techniques?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">Compétences Techniques</h3>
                    <ul>
                      {result.competences.techniques.map((c, i) => {
                        const item = formatBoldBeforeColon(c);

                        return (
                          <li key={i}>
                            <strong>{item.title}</strong>
                            {item.description && ` : ${item.description}`}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}

                {/* COMPETENCES FONCTIONNELLES */}
                {result.competences?.fonctionnelles?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">Compétences Fonctionnelles</h3>
                    <ul>
                      {result.competences.fonctionnelles.map((c, i) => {
                        const item = formatBoldBeforeColon(c);

                        return (
                          <li key={i}>
                            <strong>{item.title}</strong>
                            {item.description && ` : ${item.description}`}
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}

                {/* RADAR COMPETENCES */}
                {result.competences?.techniques?.length > 0 && (
                  <div className="result-card radar-card">
                    <h3 className="result-title">
                      <BarChart3 size={18} /> Radar des compétences
                    </h3>
                    <Radar
                      data={radarData}
                      options={{
                        responsive: true,
                        scales: {
                          r: {
                            suggestedMin: 0,
                            suggestedMax: 5,
                            ticks: { stepSize: 1 },
                          },
                        },
                        plugins: {
                          legend: { display: false },
                        },
                      }}
                    />
                  </div>
                )}

                {/* LANGUES */}
                {result.langues?.length > 0 && (
                  <div className="result-card">
                    <h3 className="result-title">🌍 Langues</h3>
                    <ul className="result-list text-gray-700">
                      {result.langues.map((l, i) => (
                        <li key={i}>{l}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* CV RECONSTITUÉ */}
                <div className="result-card cv-preview-card">
                  <h3 className="result-title">
                    <Eye size={18} /> CV reconstitué (vue synthèse)
                  </h3>
                  <div className="cv-preview-body">
                    <h4>{result.contact.nom}</h4>
                    <p className="cv-preview-contact">
                      {result.contact.email} ··· {result.contact.telephone} ···{" "}
                      {result.contact.adresse}
                    </p>

                    {/* Compétences Fonctionnelles */}
                    {result.competences?.fonctionnelles?.length > 0 && (
                      <>
                        <h4>Compétences Fonctionnelles</h4>
                        <ul>
                          {result.competences.fonctionnelles.map((c, i) => {
                            const item = formatBoldBeforeColon(c);

                            return (
                              <li key={i}>
                                <span className="underline-title">
                                  {item.title}
                                </span>
                                {item.description && ` : ${item.description}`}
                              </li>
                            );
                          })}
                        </ul>
                      </>
                    )}

                    {/* Compétences Techniques */}
                    {result.competences?.techniques?.length > 0 && (
                      <>
                        <h4>Compétences Techniques</h4>
                        <ul>
                          {result.competences.techniques.map((c, i) => {
                            const item = formatBoldBeforeColon(c);

                            return (
                              <li key={i}>
                                <span className="underline-title">
                                  {item.title}
                                </span>
                                {item.description && ` : ${item.description}`}
                              </li>
                            );
                          })}
                        </ul>
                      </>
                    )}

                    {result.formations?.length > 0 && (
                      <>
                        <h4>Formations - Certification</h4>
                        <ul>
                          {result.formations.map((f, i) => {
                            const form = formatFormationSimple(f);

                            return (
                              <li key={i} className="mb-2">
                                <strong>{form.title}</strong> :{" "}
                                {form.description}
                              </li>
                            );
                          })}
                        </ul>
                      </>
                    )}

                    {result.experiences?.length > 0 && (
                      <>
                        <h4>Expériences</h4>
                        <ul>
                          {result.experiences.map((exp, i) => (
                            <li key={i} className="mb-3">
                              {typeof exp === "string" ? (
                                // Cas Léo (inchangé)
                                (() => {
                                  const e = formatExperience(exp);
                                  return (
                                    <>
                                      <div>
                                        <strong>{e.line1}</strong>
                                      </div>
                                      {e.line2 && (
                                        <div>
                                          {e.line2.split("\n").map((l, idx) => (
                                            <div key={idx}>{l}</div>
                                          ))}
                                        </div>
                                      )}
                                    </>
                                  );
                                })()
                              ) : (
                                // Cas JLA (déjà normalisé par normalizeCvData)
                                <>
                                  <div>
                                    <strong>{exp.title}</strong>
                                  </div>

                                  {exp.bullets?.length > 0 && (
                                    <ul className="ml-4 mt-1 list-disc">
                                      {exp.bullets.map((b, j) => (
                                        <li key={j}>{b}</li>
                                      ))}
                                    </ul>
                                  )}
                                </>
                              )}
                            </li>
                          ))}
                        </ul>
                      </>
                    )}

                    {result.langues?.length > 0 && (
                      <>
                        <h4>Langues</h4>
                        <ul>
                          {result.langues.map((langue, index) => (
                            <li key={index}>{langue}</li>
                          ))}
                        </ul>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Étapes visuelles */}
          <div className="process-steps mt-16">
            <div className="process-step">
              <div className="step-icon">
                <Upload />
              </div>
              <h3 className="step-title">1. Téléversez</h3>
              <p className="step-description">
                Choisissez votre CV .docx ou .pdf
              </p>
            </div>

            <div className="process-step">
              <div className="step-icon">
                <FileText />
              </div>
              <h3 className="step-title">2. Analyse</h3>
              <p className="step-description">
                Extraction automatique des données
              </p>
            </div>

            <div className="process-step">
              <div className="step-icon">
                <ArrowRight />
              </div>
              <h3 className="step-title">3. Résultat</h3>
              <p className="step-description">Dashboard d’analyse structuré</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Start;
