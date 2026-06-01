"""UI Designer — Create UI specifications and wireframes"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class DesignSystem(Enum):
    MATERIAL = "material"
    FLUENT = "fluent"
    HUMAN_INTERFACE = "human_interface"
    CUSTOM = "custom"


@dataclass
class UIComponent:
    id: str = field(default_factory=lambda: f"COMP-{uuid.uuid4().hex[:8]}")
    name: str = ""
    component_type: str = ""
    properties: dict = field(default_factory=dict)
    states: list[str] = field(default_factory=list)
    accessibility: dict = field(default_factory=dict)
    responsive: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.component_type,
            "states": self.states,
            "accessible": self.accessibility.get("aria_label", "") != "",
        }


@dataclass
class UIPage:
    id: str = field(default_factory=lambda: f"PAGE-{uuid.uuid4().hex[:8]}")
    name: str = ""
    url: str = ""
    components: list[UIComponent] = field(default_factory=list)
    layout: str = ""
    user_flows: list[str] = field(default_factory=list)
    responsive_breakpoints: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "components_count": len(self.components),
            "layout": self.layout,
        }


@dataclass
class UISpecification:
    id: str = field(default_factory=lambda: f"UI-{uuid.uuid4().hex[:8]}")
    design_system: DesignSystem = DesignSystem.MATERIAL
    pages: list[UIPage] = field(default_factory=list)
    components: list[UIComponent] = field(default_factory=list)
    style_guide: dict = field(default_factory=dict)
    accessibility_standards: dict = field(default_factory=dict)
    responsive_design: dict = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "design_system": self.design_system.value,
            "pages_count": len(self.pages),
            "components_count": len(self.components),
            "accessibility_compliant": self.accessibility_standards.get("wcag_level", "") != "",
        }


class UIDesigner:
    """Create UI specifications and design systems."""

    def __init__(self):
        self.specifications: dict[str, UISpecification] = {}
        self.pages: dict[str, UIPage] = {}
        self.components: dict[str, UIComponent] = {}
        self.design_systems: dict[str, dict] = {
            "material": {
                "name": "Material Design",
                "colors": {
                    "primary": "#1976D2",
                    "secondary": "#FFC107",
                    "background": "#FFFFFF",
                    "surface": "#F5F5F5",
                    "error": "#D32F2F",
                },
                "typography": {
                    "font_family": "Roboto",
                    "h1": {"size": "96px", "weight": "300"},
                    "h2": {"size": "60px", "weight": "300"},
                    "body1": {"size": "16px", "weight": "400"},
                },
                "spacing": {"unit": 8, "multipliers": [0.5, 1, 2, 3, 4, 6, 8]},
            },
            "fluent": {
                "name": "Fluent Design",
                "colors": {
                    "primary": "#0078D4",
                    "secondary": "#107C10",
                    "background": "#FFFFFF",
                    "surface": "#F3F2F1",
                    "error": "#D13438",
                },
            },
        }

    def design(self, wireframes: list[dict], design_system: str = "material") -> UISpecification:
        """Design UI specifications from wireframes."""
        spec = UISpecification(
            design_system=DesignSystem(design_system) if design_system in [ds.value for ds in DesignSystem] else DesignSystem.MATERIAL
        )
        
        # Get design system properties
        ds_props = self.design_systems.get(design_system, self.design_systems["material"])
        
        # Create pages from wireframes
        for wireframe in wireframes:
            page = self._create_page(wireframe, ds_props)
            spec.pages.append(page)
            self.pages[page.id] = page
        
        # Create common components
        spec.components = self._create_common_components(ds_props)
        for comp in spec.components:
            self.components[comp.id] = comp
        
        # Set style guide
        spec.style_guide = self._create_style_guide(ds_props)
        
        # Set accessibility standards
        spec.accessibility_standards = self._create_accessibility_standards()
        
        # Set responsive design
        spec.responsive_design = self._create_responsive_design()
        
        self.specifications[spec.id] = spec
        return spec

    def _create_page(self, wireframe: dict, ds_props: dict) -> UIPage:
        """Create a UI page from wireframe."""
        page = UIPage(
            name=wireframe.get("name", "Page"),
            url=wireframe.get("url", "/"),
            layout=wireframe.get("layout", "single_column"),
        )
        
        # Create components for the page
        component_types = wireframe.get("components", ["header", "content", "footer"])
        for comp_type in component_types:
            component = self._create_component(comp_type, ds_props)
            page.components.append(component)
        
        # Set user flows
        page.user_flows = wireframe.get("user_flows", ["navigation", "interaction"])
        
        # Set responsive breakpoints
        page.responsive_breakpoints = {
            "mobile": {"max_width": "768px", "layout": "stacked"},
            "tablet": {"max_width": "1024px", "layout": "two_column"},
            "desktop": {"min_width": "1025px", "layout": "three_column"},
        }
        
        return page

    def _create_component(self, component_type: str, ds_props: dict) -> UIComponent:
        """Create a UI component."""
        component_templates = {
            "header": {
                "name": "Header",
                "states": ["default", "scrolled", "mobile"],
                "accessibility": {"role": "banner", "aria_label": "Main header"},
            },
            "navigation": {
                "name": "Navigation",
                "states": ["default", "expanded", "collapsed"],
                "accessibility": {"role": "navigation", "aria_label": "Main navigation"},
            },
            "content": {
                "name": "Content Area",
                "states": ["default", "loading", "empty", "error"],
                "accessibility": {"role": "main", "aria_label": "Main content"},
            },
            "sidebar": {
                "name": "Sidebar",
                "states": ["default", "collapsed", "hidden"],
                "accessibility": {"role": "complementary", "aria_label": "Sidebar"},
            },
            "footer": {
                "name": "Footer",
                "states": ["default", "mobile"],
                "accessibility": {"role": "contentinfo", "aria_label": "Footer"},
            },
            "button": {
                "name": "Button",
                "states": ["default", "hover", "active", "disabled", "loading"],
                "accessibility": {"role": "button"},
            },
            "input": {
                "name": "Input Field",
                "states": ["default", "focus", "error", "disabled"],
                "accessibility": {"role": "textbox"},
            },
            "card": {
                "name": "Card",
                "states": ["default", "hover", "selected"],
                "accessibility": {"role": "article"},
            },
            "modal": {
                "name": "Modal Dialog",
                "states": ["closed", "open", "closing"],
                "accessibility": {"role": "dialog", "aria_modal": "true"},
            },
            "table": {
                "name": "Data Table",
                "states": ["default", "loading", "empty", "sorted"],
                "accessibility": {"role": "table"},
            },
        }
        
        template = component_templates.get(component_type, component_templates["button"])
        
        return UIComponent(
            name=template["name"],
            component_type=component_type,
            properties=ds_props,
            states=template["states"],
            accessibility=template["accessibility"],
        )

    def _create_common_components(self, ds_props: dict) -> list[UIComponent]:
        """Create common UI components."""
        common_types = ["button", "input", "card", "modal", "table", "navigation"]
        components = []
        
        for comp_type in common_types:
            component = self._create_component(comp_type, ds_props)
            components.append(component)
        
        return components

    def _create_style_guide(self, ds_props: dict) -> dict:
        """Create comprehensive style guide."""
        return {
            "colors": ds_props.get("colors", {}),
            "typography": ds_props.get("typography", {}),
            "spacing": ds_props.get("spacing", {}),
            "icons": {
                "style": "outlined",
                "size": "24px",
                "grid": "24dp",
            },
            "animation": {
                "duration": "200ms",
                "easing": "ease-in-out",
            },
            "shadows": {
                "small": "0 1px 3px rgba(0,0,0,0.12)",
                "medium": "0 4px 6px rgba(0,0,0,0.15)",
                "large": "0 10px 20px rgba(0,0,0,0.19)",
            },
        }

    def _create_accessibility_standards(self) -> dict:
        """Create accessibility standards."""
        return {
            "wcag_level": "AA",
            "contrast_ratio": 4.5,
            "focus_indicators": True,
            "keyboard_navigation": True,
            "screen_reader_support": True,
            "aria_labels": True,
            "color_contrast": "4.5:1",
            "text_resizing": "200%",
            "motion_reduced": "respect_prefers_reduced_motion",
        }

    def _create_responsive_design(self) -> dict:
        """Create responsive design specifications."""
        return {
            "breakpoints": {
                "mobile": {"max_width": "768px"},
                "tablet": {"min_width": "769px", "max_width": "1024px"},
                "desktop": {"min_width": "1025px", "max_width": "1440px"},
                "large_desktop": {"min_width": "1441px"},
            },
            "grid_system": {
                "columns": 12,
                "gutter": "16px",
                "margin": "16px",
            },
            "typography_scale": {
                "mobile": "14px",
                "tablet": "15px",
                "desktop": "16px",
            },
        }

    def create_component_library(self, spec_id: str) -> dict:
        """Create component library from specification."""
        spec = self.specifications.get(spec_id)
        if not spec:
            return {"error": "Specification not found"}
        
        library = {
            "name": f"{spec.design_system.value.title()} Component Library",
            "components": {},
            "documentation": {},
            "examples": {},
        }
        
        for component in spec.components:
            library["components"][component.id] = {
                "name": component.name,
                "type": component.component_type,
                "properties": component.properties,
                "states": component.states,
                "accessibility": component.accessibility,
            }
            
            # Add documentation
            library["documentation"][component.id] = {
                "description": f"{component.name} component for {component.component_type}",
                "usage": f"Use {component.name.lower()} for {component.component_type} interactions",
                "variants": component.states,
                "accessibility": component.accessibility,
            }
        
        return library

    def generate_design_tokens(self, spec_id: str) -> dict:
        """Generate design tokens from specification."""
        spec = self.specifications.get(spec_id)
        if not spec:
            return {"error": "Specification not found"}
        
        tokens = {
            "colors": spec.style_guide.get("colors", {}),
            "typography": spec.style_guide.get("typography", {}),
            "spacing": spec.style_guide.get("spacing", {}),
            "shadows": spec.style_guide.get("shadows", {}),
            "animation": spec.style_guide.get("animation", {}),
            "breakpoints": spec.responsive_design.get("breakpoints", {}),
        }
        
        # Flatten tokens for CSS
        css_tokens = {}
        for category, values in tokens.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            css_tokens[f"--{category}-{key}-{sub_key}"] = sub_value
                    else:
                        css_tokens[f"--{category}-{key}"] = value
        
        tokens["css_variables"] = css_tokens
        
        return tokens

    def validate_accessibility(self, spec_id: str) -> dict:
        """Validate accessibility compliance."""
        spec = self.specifications.get(spec_id)
        if not spec:
            return {"error": "Specification not found"}
        
        issues = []
        score = 100
        
        for page in spec.pages:
            for component in page.components:
                if not component.accessibility.get("aria_label"):
                    issues.append(f"{component.name} missing aria-label")
                    score -= 5
                
                if not component.accessibility.get("role"):
                    issues.append(f"{component.name} missing ARIA role")
                    score -= 3
        
        # Check color contrast
        colors = spec.style_guide.get("colors", {})
        if len(colors) < 3:
            issues.append("Insufficient color definitions for contrast checking")
            score -= 10
        
        return {
            "compliant": score >= 80,
            "score": max(0, score),
            "issues": issues,
            "wcag_level": spec.accessibility_standards.get("wcag_level", "Unknown"),
            "recommendations": self._generate_accessibility_recommendations(issues),
        }

    def _generate_accessibility_recommendations(self, issues: list[str]) -> list[str]:
        """Generate accessibility recommendations."""
        recommendations = []
        
        for issue in issues:
            if "aria-label" in issue:
                recommendations.append("Add descriptive aria-labels to all interactive elements")
            elif "role" in issue:
                recommendations.append("Add appropriate ARIA roles for screen reader support")
            elif "contrast" in issue:
                recommendations.append("Ensure sufficient color contrast (4.5:1 minimum)")
        
        return list(set(recommendations))

    def get_design_insights(self) -> dict:
        """Get insights from all designs."""
        all_specs = list(self.specifications.values())
        
        if not all_specs:
            return {"status": "no_designs"}
        
        total_pages = sum(len(s.pages) for s in all_specs)
        total_components = sum(len(s.components) for s in all_specs)
        
        return {
            "total_specifications": len(all_specs),
            "total_pages": total_pages,
            "total_components": total_components,
            "design_systems_used": list(set(s.design_system.value for s in all_specs)),
            "accessibility_compliant": sum(1 for s in all_specs if s.accessibility_standards.get("wcag_level")),
        }