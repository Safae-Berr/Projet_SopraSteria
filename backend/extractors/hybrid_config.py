"""
Configuration AVANCÉE du Pipeline Hybride

Ce fichier permet de personnaliser le comportement du pipeline
sans modifier le code principal.
"""

from dataclasses import dataclass
from typing import Dict, Set, List
from pathlib import Path

# =============================================================================
# CONFIGURATION DES CRITÈRES DE VALIDATION
# =============================================================================

@dataclass
class ValidationConfig:
    """Configuration des critères de validation d'extraction."""

    # Critères minimums requis
    require_name: bool = True
    min_experiences: int = 1
    min_formations: int = 1
    min_skills: int = 0

    # Longueur minimale du nom
    min_name_length: int = 3
    max_name_length: int = 100

    # Détails optionnels
    require_email: bool = False
    require_phone: bool = False
    require_address: bool = False


@dataclass
class ModelConfig:
    """Configuration des modèles spaCy."""

    # Chemins des modèles (ordre de priorité)
    primary_model: Path = Path("models/cv_ner")
    backup_model: Path = Path("models/cv_pipeline")
    fallback_model: str = "fr_core_news_md"

    # Cache du modèle en mémoire
    use_cache: bool = True
    cache_ttl_seconds: int = 3600


@dataclass
class MergeConfig:
    """Configuration de la fusion des résultats."""

    # Stratégies de fusion par section
    merge_contact: str = "ml_fills_gaps"
    merge_skills: str = "union"
    merge_formations: str = "union"
    merge_experiences: str = "prefer_rules"
    merge_languages: str = "union"

    # Poids pour la sélection intelligente
    weight_rules: float = 0.6
    weight_ml: float = 0.4


class HybridExtractorConfig:
    """Configuration complète du pipeline hybride."""

    def __init__(self):
        self.validation = ValidationConfig()
        self.models = ModelConfig()
        self.merge = MergeConfig()

        # Chemins
        self.base_path = Path(__file__).parent.parent
        self.models.primary_model = self.base_path / self.models.primary_model
        self.models.backup_model = self.base_path / self.models.backup_model

        # Logging
        self.log_level: str = "INFO"
        self.verbose: bool = True


class ConfigPresets:
    """Presets de configuration pour différents cas d'usage."""

    @staticmethod
    def strict() -> HybridExtractorConfig:
        """Configuration STRICTE."""
        config = HybridExtractorConfig()
        config.validation.min_experiences = 2
        config.validation.min_formations = 1
        config.validation.min_skills = 1
        config.validation.require_email = True
        return config

    @staticmethod
    def balanced() -> HybridExtractorConfig:
        """Configuration ÉQUILIBRÉE (PAR DÉFAUT)."""
        config = HybridExtractorConfig()
        config.validation.min_experiences = 1
        config.validation.min_formations = 1
        config.validation.min_skills = 0
        return config

    @staticmethod
    def lenient() -> HybridExtractorConfig:
        """Configuration LENIENTE."""
        config = HybridExtractorConfig()
        config.validation.min_experiences = 0
        config.validation.min_formations = 0
        config.validation.min_skills = 0
        config.merge.weight_ml = 0.7
        return config


# Configuration par défaut
DEFAULT_CONFIG = HybridExtractorConfig()
STRICT_CONFIG = ConfigPresets.strict()
LENIENT_CONFIG = ConfigPresets.lenient()

