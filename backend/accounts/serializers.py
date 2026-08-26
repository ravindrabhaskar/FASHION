from django.contrib.auth import get_user_model
from rest_framework import serializers

from accounts.models import PhoneOTP

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, trim_whitespace=False)

    class Meta:
        model = User
        fields = ("email", "full_name", "password")

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            full_name=validated_data["full_name"].strip(),
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)


class SocialLoginSerializer(serializers.Serializer):
    provider = serializers.ChoiceField(choices=["google", "apple"])
    id_token = serializers.CharField()


class DeviceInfoMixin(serializers.Serializer):
    device_name = serializers.CharField(required=False, allow_blank=True, max_length=120, default="")


class OTPRequestSerializer(serializers.Serializer):
    phone = serializers.RegexField(r"^\+?[0-9]{10,15}$")
    purpose = serializers.ChoiceField(choices=PhoneOTP.Purpose.values)


class OTPVerifyLoginSerializer(serializers.Serializer):
    phone = serializers.RegexField(r"^\+?[0-9]{10,15}$")
    code = serializers.CharField(min_length=6, max_length=6)
    full_name = serializers.CharField(required=False, allow_blank=True, max_length=120)


class MeSerializer(serializers.ModelSerializer):
    onboarding_completed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id", "email", "full_name", "phone", "role", "status", "avatar",
            "onboarding_completed_at", "onboarding_completed", "created_at",
        )
        read_only_fields = fields

    def get_onboarding_completed(self, obj) -> bool:
        return obj.onboarding_completed_at is not None


class UpdateMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("full_name", "avatar")


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(trim_whitespace=False)
    new_password = serializers.CharField(min_length=8, trim_whitespace=False)


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8, trim_whitespace=False)


class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(trim_whitespace=False)
