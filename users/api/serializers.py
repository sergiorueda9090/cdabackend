from rest_framework import serializers
from users.models import User
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'password', 'is_staff', 'is_active', 'is_superuser', 'image']
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},  # El password es opcional
            'email': {'required': True},
            'username': {'required': True}
        }

    def validate_email(self, value):
        # Validar formato del correo y si ya existe (excluyendo al usuario actual)
        if self.instance:
            if User.objects.filter(email=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("El correo ya está registrado.")
        elif User.objects.filter(email=value).exists():
            raise serializers.ValidationError("El correo ya está registrado.")
        return value

    def validate_username(self, value):
        # Validar si el nombre de usuario ya existe (excluyendo al usuario actual)
        if self.instance:
            if User.objects.filter(username=value).exclude(id=self.instance.id).exists():
                raise serializers.ValidationError("El nombre de usuario ya está en uso.")
        elif User.objects.filter(username=value).exists():
            raise serializers.ValidationError("El nombre de usuario ya está en uso.")
        return value

    def create(self, validated_data):
        # Crear el usuario con contraseña encriptada
        user = User.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        # Extraer el campo `password` de los datos validados, si está presente
        password = validated_data.pop('password', None)

        # Actualizar los campos normales
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Si se envió una contraseña, actualízala de forma segura
        if password:
            instance.set_password(password)

        # Guardar los cambios en la base de datos
        instance.save()
        return instance