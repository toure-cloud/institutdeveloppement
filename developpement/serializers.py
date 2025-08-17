from rest_framework import serializers
from .models import TeamMember, Expertise


class ExpertiseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expertise
        fields = ["name"]


class TeamMemberSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    category_display = serializers.CharField(
        source="get_category_display", read_only=True
    )
    expertises = ExpertiseSerializer(many=True, read_only=True)
    active_social_links = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()

    class Meta:
        model = TeamMember
        fields = [
            "id",
            "slug",
            "full_name",
            "title",
            "bio",
            "category",
            "category_display",
            "photo",
            "expertises",
            "active_social_links",
        ]

    def get_active_social_links(self, obj):
        # Retourne uniquement les liens non vides
        return {
            "linkedin": obj.linkedin_url if obj.linkedin_url else None,
            "researchgate": obj.researchgate_url if obj.researchgate_url else None,
        }

    def get_photo(self, obj):
        # Retourne l'URL complète de la photo ou None
        request = self.context.get("request")
        if obj.photo:
            return (
                request.build_absolute_uri(obj.photo.url) if request else obj.photo.url
            )
        return None
    