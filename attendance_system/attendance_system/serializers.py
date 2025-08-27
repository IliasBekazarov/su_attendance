from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        # Токен payload'уна role кошуу
        refresh = self.get_token(self.user)
        refresh['role'] = self.user.role
        data['refresh'] = str(refresh)
        data['access'] = str(refresh.access_token)
        return data