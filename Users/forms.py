from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django import forms
from django.contrib.auth.models import User
from .models import Profile




class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full px-4 py-2 bg-white bg-opacity-5 border border-white border-opacity-10 rounded-lg text-white placeholder-white placeholder-opacity-40'
            })


class UserUpdateForm(forms.ModelForm):
        class Meta:
            model = User
            fields = ["username", "email"]

class ProfileUpdateForm(forms.ModelForm):
     class Meta:
          model = Profile
          fields = ['profile_image']
  