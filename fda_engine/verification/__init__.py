"""Verification engine — parameter extraction, triangulation, conflict detection, cascade updates."""
from fda_engine.verification.entity_extractor import EntityExtractor
from fda_engine.verification.triangulation import TriangulationEngine
from fda_engine.verification.conflict import ConflictDetector
from fda_engine.verification.cascade import CascadeUpdater

__all__ = [
    "EntityExtractor",
    "TriangulationEngine",
    "ConflictDetector",
    "CascadeUpdater",
]
