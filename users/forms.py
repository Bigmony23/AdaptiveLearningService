from django import forms

from users.models import CustomUser
from django.utils import timezone
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate
from .models import CustomUser
from datetime import timedelta

class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя'
        })
    )
    last_name = forms.CharField(
        label='Фамилия',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите фамилию'
        })
    )
    first_name = forms.CharField(
        label='Имя',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя'
        })
    )
    patronymic = forms.CharField(
        label='Отчество',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите отчество'
        })
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@mail.com'
        })
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Повторите пароль'
        })
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'last_name', 'first_name', 'patronymic', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.patronymic = self.cleaned_data.get('patronymic', '')
        if commit:
            user.save()
        return user



class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите имя пользователя'
        })
    )

    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        # Проверяем существование пользователя
        try:
            user = CustomUser.objects.get(username=username)

            # Пользователь существует, но не активирован
            if not user.is_active:

                registration_age = timezone.now() - user.date_joined

                if registration_age >= timedelta(days=2):
                    raise forms.ValidationError(
                        'Ваш аккаунт находится на проверке более 2 дней. '
                        'Пожалуйста, обратитесь в техническую поддержку.'
                        'admin@mail.ru'
                    )

                raise forms.ValidationError(
                    'Ваш аккаунт находится на проверке администратором.'
                )

        except CustomUser.DoesNotExist:
            pass

        # Стандартная авторизация
        self.user_cache = authenticate(
            self.request,
            username=username,
            password=password
        )

        if self.user_cache is None:
            raise forms.ValidationError(
                'Неверное имя пользователя или пароль.'
            )

        return self.cleaned_data