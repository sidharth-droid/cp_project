from django import forms
from .models import Complains,Attachment
from django.forms import inlineformset_factory
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
        fields = ['ack_number','name','mobile_number','email','address','fraud_type','steps_taken','status','investigating_officer']
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