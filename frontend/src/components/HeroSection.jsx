import React from "react";
import { NavLink } from "react-router-dom";
import { ArrowRight, FileText } from "lucide-react";
import heroImage from "../assets/images/hero-cv.png";
import sopra from "../assets/logos/sopra-steria-logo.svg";

const HeroSection = () => {
  return (
    <section className="hero-section">
      {/* Cercles décoratifs */}
      <div className="hero-decor">
        <div className="decor-circle decor-circle-left"></div>
        <div className="decor-circle decor-circle-right"></div>
      </div>

      <div className="hero-container">
        <div className="hero-grid">
          {/* Colonne gauche */}
          <div className="text-content">
            <div className="hero-logo">
              <img src={sopra} alt="Sopra Steria" />
            </div>

            <h1 className="hero-title">
              Transformez vos CV en{" "}
              <span className="gradient-text">documents standardisés</span>
            </h1>

            <p className="hero-subtitle">
              Extrayez automatiquement les informations de n'importe quel CV et
              générez des documents professionnels standardisés en quelques
              secondes.
            </p>

            <div className="hero-buttons">
              <NavLink to="/start" className="btn-primary group">
                Commencer maintenant
                <ArrowRight className="w-5 h-5 transition-transform duration-300 group-hover:translate-x-1" />
              </NavLink>

              <NavLink to="/example" className="btn-secondary">
                <FileText className="w-5 h-5" />
                Voir un exemple
              </NavLink>
            </div>

            <div className="hero-stats">
              <div>
                <div className="stat-value orange">16</div>
                <div className="stat-label">CV traités</div>
              </div>
              <div>
                <div className="stat-value red">90%</div>
                <div className="stat-label">Précision</div>
              </div>
              <div>
                <div className="stat-value light-orange">2min</div>
                <div className="stat-label">Temps moyen</div>
              </div>
            </div>
          </div>

          {/* Image droite */}
          <div className="hero-image-container">
            <div className="hero-image-wrapper">
              <img src={heroImage} alt="Visualisation de CV" />
              <div className="image-overlay"></div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default HeroSection;
