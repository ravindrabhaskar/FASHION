from rest_framework import serializers

from fashion.registry import get_occasion
from profiles.models import StyleProfile, UserProfile

VALID_STYLE_TAGS = {
    "minimal", "classic", "streetwear", "bohemian", "ethnic-traditional",
    "fusion", "formal-business", "smart-casual", "sporty-athleisure",
    "romantic", "edgy", "vintage", "coastal", "preppy",
}


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("display_name", "bio", "city", "gender", "date_of_birth", "height_cm", "language")


class StyleProfileSerializer(serializers.ModelSerializer):
    completion = serializers.SerializerMethodField()

    class Meta:
        model = StyleProfile
        fields = (
            "preferred_styles", "favorite_colors", "avoided_colors", "fit_preference",
            "budget_min", "budget_max", "clothing_preferences", "common_occasions",
            "traditional_modern_balance", "completion",
        )
        read_only_fields = ("completion",)

    def validate_preferred_styles(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Expected a list of style tags.")
        invalid = [s for s in value if s not in VALID_STYLE_TAGS]
        if invalid:
            raise serializers.ValidationError(f"Unknown style tags: {', '.join(invalid)}")
        return list(dict.fromkeys(value))[:8]

    def validate_common_occasions(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Expected a list of occasion slugs.")
        unknown = [o for o in value if not get_occasion(o)]
        if unknown:
            raise serializers.ValidationError(f"Unknown occasions: {', '.join(unknown)}")
        return list(dict.fromkeys(value))[:10]

    def validate(self, attrs):
        budget_min = attrs.get("budget_min", getattr(self.instance, "budget_min", None))
        budget_max = attrs.get("budget_max", getattr(self.instance, "budget_max", None))
        if budget_min is not None and budget_max is not None and budget_min > budget_max:
            raise serializers.ValidationError({"budget_min": "Minimum budget cannot exceed maximum."})
        return attrs

    def get_completion(self, obj) -> int:
        return obj.compute_completion()
