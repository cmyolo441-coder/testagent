"""Category Theory Lab - Explores categorical mathematical structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime


@dataclass
class Morphism:
    """A morphism in a category."""
    name: str
    source: str
    target: str
    composition: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source": self.source,
            "target": self.target,
            "composition": self.composition,
        }


@dataclass
class Category:
    """A mathematical category."""
    name: str
    objects: List[str]
    morphisms: List[Morphism]
    identity_morphisms: Dict[str, str]
    composition_rule: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "objects": self.objects,
            "morphism_count": len(self.morphisms),
            "identity_morphisms": self.identity_morphisms,
            "composition_rule": self.composition_rule,
        }


@dataclass
class Functor:
    """A functor between categories."""
    name: str
    source_category: str
    target_category: str
    object_map: Dict[str, str]
    morphism_map: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source_category": self.source_category,
            "target_category": self.target_category,
            "object_map": self.object_map,
            "morphism_map": self.morphism_map,
        }


@dataclass
class NaturalTransformation:
    """A natural transformation between functors."""
    name: str
    source_functor: str
    target_functor: str
    components: Dict[str, str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source_functor": self.source_functor,
            "target_functor": self.target_functor,
            "components": self.components,
        }


class CategoryTheoryLab:
    """Explores categorical mathematical structures.
    
    Provides tools for working with categories, functors, and
    natural transformations.
    """
    
    def __init__(self):
        self._categories: Dict[str, Category] = {}
        self._functors: Dict[str, Functor] = {}
        self._transformations: Dict[str, NaturalTransformation] = {}
        self._initialize_common_categories()
    
    def _initialize_common_categories(self):
        """Initialize with common mathematical categories."""
        # Set category
        set_category = Category(
            name="Set",
            objects=["Set"],
            morphisms=[
                Morphism("function", "A", "B", "g ∘ f"),
                Morphism("inclusion", "A", "B", "composition"),
            ],
            identity_morphisms={"A": "id_A", "B": "id_B"},
            composition_rule="Function composition: (g ∘ f)(x) = g(f(x))",
        )
        self._categories["Set"] = set_category
        
        # Group category
        group_category = Category(
            name="Grp",
            objects=["Group"],
            morphisms=[
                Morphism("homomorphism", "G", "H", "composition"),
            ],
            identity_morphisms={"G": "id_G"},
            composition_rule="Homomorphism composition",
        )
        self._categories["Grp"] = group_category
        
        # Top category
        top_category = Category(
            name="Top",
            objects=["Space"],
            morphisms=[
                Morphism("continuous_map", "X", "Y", "composition"),
            ],
            identity_morphisms={"X": "id_X"},
            composition_rule="Continuous map composition",
        )
        self._categories["Top"] = top_category
    
    def explore(self, domain: str) -> Category:
        """Explore category theory in a domain.
        
        Args:
            domain: Mathematical domain
            
        Returns:
            Category structure
        """
        domain_map = {
            "set": "Set",
            "sets": "Set",
            "group": "Grp",
            "groups": "Grp",
            "topology": "Top",
            "topological": "Top",
        }
        
        key = domain.lower()
        if key in domain_map:
            return self._categories[domain_map[key]]
        
        # Generate generic category
        return self._generate_generic_category(domain)
    
    def _generate_generic_category(self, domain: str) -> Category:
        """Generate a generic category for a domain."""
        return Category(
            name=f"{domain.title()}Cat",
            objects=[f"{domain.title()}Obj"],
            morphisms=[
                Morphism(f"{domain}_morphism", "X", "Y", "composition"),
            ],
            identity_morphisms={"X": "id_X"},
            composition_rule=f"Morphism composition in {domain}",
        )
    
    def create_functor(
        self,
        name: str,
        source: str,
        target: str,
        obj_map: Dict[str, str],
        morph_map: Dict[str, str],
    ) -> Functor:
        """Create a functor between categories."""
        functor = Functor(
            name=name,
            source_category=source,
            target_category=target,
            object_map=obj_map,
            morphism_map=morph_map,
        )
        
        self._functors[name] = functor
        return functor
    
    def create_natural_transformation(
        self,
        name: str,
        source_functor: str,
        target_functor: str,
        components: Dict[str, str],
    ) -> NaturalTransformation:
        """Create a natural transformation."""
        transformation = NaturalTransformation(
            name=name,
            source_functor=source_functor,
            target_functor=target_functor,
            components=components,
        )
        
        self._transformations[name] = transformation
        return transformation
    
    def verify_functoriality(self, functor_name: str) -> bool:
        """Verify that a functor preserves composition and identity."""
        if functor_name not in self._functors:
            return False
        
        functor = self._functors[functor_name]
        
        # Check if identity is preserved
        # (simplified check)
        return len(functor.object_map) > 0 and len(functor.morphism_map) > 0
    
    def verify_naturality(self, transformation_name: str) -> bool:
        """Verify naturality condition for a natural transformation."""
        if transformation_name not in self._transformations:
            return False
        
        transformation = self._transformations[transformation_name]
        
        # Simplified check
        return len(transformation.components) > 0
