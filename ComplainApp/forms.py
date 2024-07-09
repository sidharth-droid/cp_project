from django import forms
from .models import Complains,Attachment
from django.forms import inlineformset_factory
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
class ComplainsForm(forms.ModelForm):
    mobile_number = forms.CharField(help_text="Enter multiple mobile numbers separated by commas")
    class Meta:
        model = Complains
        fields = ['ack_number','mobile_number','name','address','email','fraud_type','steps_taken','status','investigating_officer']
    def clean_mobile(self):
        mobile_numbers = self.cleaned_data['mobile_number']
        return mobile_numbers
    
class AdminLoginForm(forms.Form):
    username=forms.CharField(max_length=150,widget=forms.TextInput(attrs={
        'class':'validate',
        'placeholder':'username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'validate',
        'placeholder': 'Password'
    }))
class ComplainForm(forms.ModelForm):
    class Meta:
        model = Complains
        fields = ['name','mobile_number','email','address','fraud_type','steps_taken','status','description','accusedAccountNumbers','accusedSuspiciousItem','investigating_officer']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'validate'}),
            'mobile_number': forms.Textarea(attrs={'class': 'materialize-textarea', 'help_text': 'Enter Mobile Numbers'}),
            'address': forms.Textarea(attrs={'class': 'materialize-textarea', 'help_text': 'Enter Address'}),
            'email': forms.EmailInput(),
            'fraud_type': forms.Textarea(attrs={'class': 'materialize-textarea', 'help_text': 'Enter Type of Fraud'}),
            'steps_taken': forms.Textarea(attrs={'class': 'materialize-textarea'}),
            # 'images_videos': forms.FileInput(),
            'status': forms.Select(choices=[('open', 'Open'), ('in review', 'In Review'), ('visit ps', 'Visit Police Station'), 
                                            ('in progress', 'In Progress'), ('closed', 'Closed (Reach out to Police Station)')],
                                 attrs={'class': 'validate'}),
            'investigating_officer': forms.TextInput(attrs={'class': 'validate'}),
        }
class AttachmentForm(forms.ModelForm):
    class Meta:
        model = Attachment
        fields = ['file']

AttachmentFormSet = inlineformset_factory(
    Complains, Attachment, form=AttachmentForm, extra=1, can_delete=True
)

class CustomUserCreationForm(UserCreationForm):
    # class Meta(UserCreationForm.Meta):
    #     model = User
    #     fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_active']
    email = forms.EmailField(required=False)  # Email is optional
    is_active = forms.BooleanField(required=False, initial=True, label="Active")
    is_staff = forms.BooleanField(required=False, initial=False, label="Staff")


    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_active']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')  # Handle optional email
        # user.is_active = self.cleaned_data['is_active']
        # user.is_staff = self.cleaned_data.get['is_staff']
        user.is_active = self.cleaned_data.get('is_active', True)
        user.is_staff = self.cleaned_data.get('is_staff', True)
        if commit:
            user.save()
        return user
# Form for User update
class CustomUserChangeForm(UserChangeForm):
    password = None  # Disable password field
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']
    
# Form for Group creation and update
class GroupForm(forms.ModelForm):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    class Meta:
        model = Group
        fields = ['name', 'permissions', 'users']

    def save(self, commit=True):
        group = super().save(commit=False)
        if commit:
            group.save()
            self.save_m2m()
            group.user_set.set(self.cleaned_data['users'])
        return group

