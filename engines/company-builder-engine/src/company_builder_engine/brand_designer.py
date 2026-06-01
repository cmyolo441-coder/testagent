"""Brand Designer — Create brand identity systems"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum
import uuid
from datetime import datetime


class BrandPersonality(Enum):
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    INNOVATIVE = "innovative"
    TRUSTWORTHY = "trustworthy"
    BOLD = "bold"
    MINIMALIST = "minimalist"


@dataclass
class BrandColors:
    primary: str = ""
    secondary: str = ""
    accent: str = ""
    background: str = ""
    text: str = ""
    success: str = ""
    warning: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "accent": self.accent,
            "background": self.background,
            "text": self.text,
        }


@dataclass
class BrandTypography:
    primary_font: str = ""
    secondary_font: str = ""
    heading_weight: str = ""
    body_weight: str = ""
    line_height: float = 0
    letter_spacing: str = ""

    def to_dict(self) -> dict:
        return {
            "primary_font": self.primary_font,
            "secondary_font": self.secondary_font,
            "heading_weight": self.heading_weight,
            "body_weight": self.body_weight,
        }


@dataclass
class BrandVoice:
    tone: str = ""
    style: str = ""
    vocabulary: list[str] = field(default_factory=list)
    do_not_use: list[str] = field(default_factory=list)
    examples: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tone": self.tone,
            "style": self.style,
            "vocabulary_count": len(self.vocabulary),
        }


@dataclass
class BrandIdentity:
    id: str = field(default_factory=lambda: f"BRAND-{uuid.uuid4().hex[:8]}")
    company_name: str = ""
    tagline: str = ""
    personality: BrandPersonality = BrandPersonality.PROFESSIONAL
    colors: BrandColors = field(default_factory=BrandColors)
    typography: BrandTypography = field(default_factory=BrandTypography)
    voice: BrandVoice = field(default_factory=BrandVoice)
    logo_concepts: list[dict] = field(default_factory=list)
    brand_guidelines: dict = field(default_factory=dict)
    values: list[str] = field(default_factory=list)
    mission_statement: str = ""
    vision_statement: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "company_name": self.company_name,
            "tagline": self.tagline,
            "personality": self.personality.value,
            "colors": self.colors.to_dict(),
            "typography": self.typography.to_dict(),
            "voice": self.voice.to_dict(),
            "values_count": len(self.values),
        }


class BrandDesigner:
    """Create comprehensive brand identity systems."""

    def __init__(self):
        self.identities: dict[str, BrandIdentity] = {}
        self.brand_palettes: dict[str, dict] = {
            "tech": {
                "primary": "#0066CC",
                "secondary": "#00A651",
                "accent": "#FF6B35",
                "background": "#FFFFFF",
                "text": "#1A1A1A",
            },
            "finance": {
                "primary": "#003366",
                "secondary": "#006699",
                "accent": "#FFD700",
                "background": "#F8F9FA",
                "text": "#2C3E50",
            },
            "healthcare": {
                "primary": "#0077B6",
                "secondary": "#00B4D8",
                "accent": "#90E0EF",
                "background": "#FFFFFF",
                "text": "#023E8A",
            },
            "education": {
                "primary": "#6A040F",
                "secondary": "#D00000",
                "accent": "#FFBA08",
                "background": "#FFFFFF",
                "text": "#370617",
            },
        }

    def design(self, company_name: str, values: list[str], industry: str = "tech") -> BrandIdentity:
        """Design brand identity based on company values and industry."""
        identity = BrandIdentity(
            company_name=company_name,
            values=values,
        )
        
        # Determine brand personality based on values
        identity.personality = self._determine_personality(values)
        
        # Create color palette
        identity.colors = self._create_color_palette(industry, values)
        
        # Create typography
        identity.typography = self._create_typography(identity.personality)
        
        # Create brand voice
        identity.voice = self._create_voice(values, identity.personality)
        
        # Create tagline
        identity.tagline = self._create_tagline(company_name, values)
        
        # Create mission and vision
        identity.mission_statement = self._create_mission(values)
        identity.vision_statement = self._create_vision(values)
        
        # Create logo concepts
        identity.logo_concepts = self._create_logo_concepts(company_name, identity.colors, identity.personality)
        
        # Create brand guidelines
        identity.brand_guidelines = self._create_brand_guidelines(identity)
        
        self.identities[identity.id] = identity
        return identity

    def _determine_personality(self, values: list[str]) -> BrandPersonality:
        """Determine brand personality from values."""
        personality_map = {
            "innovation": BrandPersonality.INNOVATIVE,
            "trust": BrandPersonality.TRUSTWORTHY,
            "quality": BrandPersonality.PROFESSIONAL,
            "friendliness": BrandPersonality.FRIENDLY,
            "boldness": BrandPersonality.BOLD,
            "simplicity": BrandPersonality.MINIMALIST,
        }
        
        for value in values:
            for keyword, personality in personality_map.items():
                if keyword in value.lower():
                    return personality
        
        return BrandPersonality.PROFESSIONAL

    def _create_color_palette(self, industry: str, values: list[str]) -> BrandColors:
        """Create color palette based on industry and values."""
        base_palette = self.brand_palettes.get(industry, self.brand_palettes["tech"])
        
        colors = BrandColors(
            primary=base_palette["primary"],
            secondary=base_palette["secondary"],
            accent=base_palette["accent"],
            background=base_palette["background"],
            text=base_palette["text"],
            success="#28A745",
            warning="#FFC107",
            error="#DC3545",
        )
        
        # Adjust colors based on values
        if "energy" in [v.lower() for v in values]:
            colors.accent = "#FF4500"
        if "calm" in [v.lower() for v in values]:
            colors.primary = "#4A90E2"
        
        return colors

    def _create_typography(self, personality: BrandPersonality) -> BrandTypography:
        """Create typography system based on personality."""
        typography_map = {
            BrandPersonality.PROFESSIONAL: BrandTypography(
                primary_font="Inter",
                secondary_font="Roboto",
                heading_weight="700",
                body_weight="400",
                line_height=1.6,
                letter_spacing="0",
            ),
            BrandPersonality.FRIENDLY: BrandTypography(
                primary_font="Nunito",
                secondary_font="Open Sans",
                heading_weight="600",
                body_weight="400",
                line_height=1.7,
                letter_spacing="0.01em",
            ),
            BrandPersonality.INNOVATIVE: BrandTypography(
                primary_font="Space Grotesk",
                secondary_font="DM Sans",
                heading_weight="700",
                body_weight="400",
                line_height=1.5,
                letter_spacing="-0.02em",
            ),
            BrandPersonality.TRUSTWORTHY: BrandTypography(
                primary_font="Merriweather",
                secondary_font="Source Sans Pro",
                heading_weight="700",
                body_weight="400",
                line_height=1.8,
                letter_spacing="0",
            ),
            BrandPersonality.BOLD: BrandTypography(
                primary_font="Montserrat",
                secondary_font="Poppins",
                heading_weight="800",
                body_weight="400",
                line_height=1.4,
                letter_spacing="-0.01em",
            ),
            BrandPersonality.MINIMALIST: BrandTypography(
                primary_font="Helvetica Neue",
                secondary_font="Arial",
                heading_weight="500",
                body_weight="300",
                line_height=1.6,
                letter_spacing="0.02em",
            ),
        }
        
        return typography_map.get(personality, typography_map[BrandPersonality.PROFESSIONAL])

    def _create_voice(self, values: list[str], personality: BrandPersonality) -> BrandVoice:
        """Create brand voice based on values and personality."""
        voice_map = {
            BrandPersonality.PROFESSIONAL: BrandVoice(
                tone="authoritative yet approachable",
                style="clear and concise",
                vocabulary=["innovative", "reliable", "efficient", "expert"],
                do_not_use=["slang", "jargon", "overly casual language"],
            ),
            BrandPersonality.FRIENDLY: BrandVoice(
                tone="warm and inviting",
                style="conversational and helpful",
                vocabulary=["we", "together", "easy", "simple"],
                do_not_use=["technical jargon", "formal language", "complex sentences"],
            ),
            BrandPersonality.INNOVATIVE: BrandVoice(
                tone="forward-thinking and inspiring",
                style="dynamic and visionary",
                vocabulary=["future", "transform", "pioneer", "revolutionary"],
                do_not_use=["traditional", "outdated", "boring"],
            ),
            BrandPersonality.TRUSTWORTHY: BrandVoice(
                tone="reliable and dependable",
                style="straightforward and honest",
                vocabulary=["proven", "secure", "guaranteed", "trusted"],
                do_not_use=["exaggeration", "unsubstantiated claims", "vague promises"],
            ),
            BrandPersonality.BOLD: BrandVoice(
                tone="confident and assertive",
                style="direct and impactful",
                vocabulary=["powerful", "unstoppable", "dominant", "leading"],
                do_not_use=["timid", "uncertain", "apologetic"],
            ),
            BrandPersonality.MINIMALIST: BrandVoice(
                tone="clean and simple",
                style="minimal and focused",
                vocabulary=["essential", "pure", "simple", "clarity"],
                do_not_use=["unnecessary words", "complex phrases", "decorative language"],
            ),
        }
        
        voice = voice_map.get(personality, voice_map[BrandPersonality.PROFESSIONAL])
        
        # Add examples based on tone
        voice.examples = [
            {"context": "website", "text": f"We make {', '.join(voice.vocabulary[:2])} solutions"},
            {"context": "social", "text": f"Experience the power of {voice.vocabulary[0] if voice.vocabulary else 'innovation'}"},
        ]
        
        return voice

    def _create_tagline(self, company_name: str, values: list[str]) -> str:
        """Create a memorable tagline."""
        tagline_templates = [
            f"{company_name}: {values[0].title()} Redefined" if values else f"{company_name}: Innovation Matters",
            f"Empowering {values[0].lower() if values else 'innovation'} through {company_name}",
            f"{company_name}: Where {values[0].title() if values else 'Innovation'} Meets Reality",
        ]
        
        import random
        return random.choice(tagline_templates)

    def _create_mission(self, values: list[str]) -> str:
        """Create mission statement."""
        value_text = ", ".join(values[:3]) if values else "innovation, quality, and customer success"
        return f"Our mission is to deliver exceptional value through {value_text}, empowering our customers to achieve their goals."

    def _create_vision(self, values: list[str]) -> str:
        """Create vision statement."""
        return "To be the industry leader in innovative solutions, setting new standards for excellence and customer satisfaction."

    def _create_logo_concepts(self, company_name: str, colors: BrandColors, personality: BrandPersonality) -> list[dict]:
        """Create logo concepts."""
        concepts = [
            {
                "name": "Wordmark",
                "description": f"Clean wordmark using {colors.primary}",
                "style": "modern",
                "colors": [colors.primary, colors.text],
            },
            {
                "name": "Abstract Symbol",
                "description": "Abstract symbol representing core values",
                "style": "symbolic",
                "colors": [colors.primary, colors.secondary],
            },
            {
                "name": "Combination Mark",
                "description": "Symbol with company name",
                "style": "combination",
                "colors": [colors.primary, colors.secondary, colors.accent],
            },
        ]
        
        return concepts

    def _create_brand_guidelines(self, identity: BrandIdentity) -> dict:
        """Create comprehensive brand guidelines."""
        return {
            "logo_usage": {
                "minimum_size": "24px height",
                "clear_space": "1x logo height",
                "variants": ["full color", "monochrome", "reversed"],
            },
            "color_usage": {
                "primary": "Headlines, CTAs, key elements",
                "secondary": "Supporting elements, backgrounds",
                "accent": "Highlights, notifications, links",
                "text": "Body text, secondary information",
            },
            "typography_usage": {
                "headings": identity.typography.primary_font,
                "body": identity.typography.secondary_font,
                "sizes": {"h1": "48px", "h2": "36px", "h3": "24px", "body": "16px"},
            },
            "voice_guidelines": {
                "tone": identity.voice.tone,
                "style": identity.voice.style,
                "do_not_use": identity.voice.do_not_use,
            },
            "imagery_style": {
                "photography": "High-quality, authentic images",
                "illustrations": "Clean, modern style",
                "icons": "Consistent line weight, minimal",
            },
        }

    def create_brand_kit(self, identity_id: str) -> dict:
        """Create downloadable brand kit."""
        identity = self.identities.get(identity_id)
        if not identity:
            return {"error": "Identity not found"}
        
        brand_kit = {
            "company_name": identity.company_name,
            "tagline": identity.tagline,
            "colors": {
                "hex": identity.colors.to_dict(),
                "rgb": self._hex_to_rgb(identity.colors.primary),
            },
            "typography": identity.typography.to_dict(),
            "logo_files": [
                {"format": "svg", "usage": "Web and print"},
                {"format": "png", "usage": "Digital applications"},
                {"format": "pdf", "usage": "Print materials"},
            ],
            "guidelines": identity.brand_guidelines,
            "templates": {
                "business_card": {"width": "3.5in", "height": "2in"},
                "letterhead": {"width": "8.5in", "height": "11in"},
                "social_media": {"profile": "400x400", "cover": "1500x500"},
            },
        }
        
        return brand_kit

    def _hex_to_rgb(self, hex_color: str) -> dict:
        """Convert hex color to RGB."""
        hex_color = hex_color.lstrip("#")
        return {
            "r": int(hex_color[0:2], 16),
            "g": int(hex_color[2:4], 16),
            "b": int(hex_color[4:6], 16),
        }

    def validate_brand_consistency(self, identity_id: str, content_samples: list[str]) -> dict:
        """Validate brand consistency across content samples."""
        identity = self.identities.get(identity_id)
        if not identity:
            return {"error": "Identity not found"}
        
        issues = []
        score = 100
        
        for sample in content_samples:
            # Check tone consistency
            sample_lower = sample.lower()
            for word in identity.voice.do_not_use:
                if word.lower() in sample_lower:
                    issues.append(f"Content contains discouraged word: {word}")
                    score -= 10
            
            # Check vocabulary usage
            if not any(v.lower() in sample_lower for v in identity.voice.vocabulary):
                issues.append("Content doesn't use brand vocabulary")
                score -= 5
        
        return {
            "consistent": score >= 80,
            "score": max(0, score),
            "issues": issues,
            "recommendations": [
                f"Use brand voice: {identity.voice.tone}",
                f"Include vocabulary: {', '.join(identity.voice.vocabulary[:3])}",
                f"Avoid: {', '.join(identity.voice.do_not_use[:3])}",
            ],
        }

    def get_brand_insights(self) -> dict:
        """Get insights from all brand identities."""
        all_identities = list(self.identities.values())
        
        if not all_identities:
            return {"status": "no_brands"}
        
        personalities = {}
        for identity in all_identities:
            p = identity.personality.value
            personalities[p] = personalities.get(p, 0) + 1
        
        return {
            "total_brands": len(all_identities),
            "personalities": personalities,
            "industries_covered": len(set(i.values[0] if i.values else "general" for i in all_identities)),
            "average_values_per_brand": sum(len(i.values) for i in all_identities) / len(all_identities),
        }