from django import forms
from .models import Complains,FIR
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User, Group
from django_select2.forms import Select2MultipleWidget
from cloudinary.forms import CloudinaryFileField
class ComplainsForm(forms.ModelForm):
    mobile_number = forms.CharField(help_text="Enter multiple mobile numbers separated by commas")
    class Meta:
        model = Complains
        fields = ['ack_number','mobile_number','name','address','email','fraud_type','steps_taken','status','enquiry_officer']
    def clean_mobile(self):
        mobile_numbers = self.cleaned_data['mobile_number']
        return mobile_numbers
class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6, required=True)
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
        
        fields = ['name','mobile_number','email','address','fraud_type','description','place_of_incidence','suspect_account_numbers','suspect_emails','suspect_links','suspect_mobile_numbers','fraudlent_amount','amount_recovered','steps_taken','status','enquiry_officer','message','upload_status','files']
    def __init__(self, *args, **kwargs):
        super(ComplainForm, self).__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields.pop('files')

# class ComplainFileForm(forms.ModelForm):
#     file = CloudinaryFileField()
#     class Meta:
#         model = ComplainFile
#         fields = ['file']
    # def __init__(self,*args,**kwargs):
    #     super().__init__(*args,**kwargs)
    #     self.fields['file'].options={
    #         'tags':'new_image',
            
    #     }    
class FIRForm(forms.ModelForm):
    # complain = forms.ModelChoiceField(queryset=Complains.objects.all(), empty_label="Select a Complain")
    # complain = forms.ModelChoiceField(queryset=Complains.objects.all(), empty_label="Select a Complain",widget=ModelSelect2Widget(model=Complains,search_fields=['name__icontains','mobile_number__icontains']))
    complain = forms.ModelMultipleChoiceField(
        queryset=Complains.objects.all(),
        widget=Select2MultipleWidget,
        label="Select Complains"
    )
    date_reported = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S'],
        required=False
    )
    date_of_dispatch_from_ps = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S'],
        required=False
    )
    class Meta:
        model = FIR
        fields = ['complain','fir_number', 'date_reported', 'place_of_occurrence', 'distance', 'direction', 
                  'date_of_dispatch_from_ps', 'name_of_complainant', 'residence_of_complainant', 
                  'name_of_accused', 'residence_of_accused', 'description', 'section', 
                  'steps_taken_by_io', 'result_of_the_case']
        widgets = {
            'complain': Select2MultipleWidget
        }
    def clean_complain(self):
        selected_complains = self.cleaned_data['complain']
        ack_numbers = [complain.ack_number for complain in selected_complains]
        # ack_numbers = ""
        # for complain in selected_complains:
        #     ack_numbers+=complain.ack_number
        return ack_numbers
    # def save(self, commit=True):
    #     # Override save method if needed
    #     instance = super().save(commit=False)
    #     if commit:
    #         instance.save()
    #     return instance
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['complain'].label_from_instance = lambda obj: obj.Date
        
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=False)
    is_active = forms.BooleanField(required=False, initial=True, label="Active")
    is_staff = forms.BooleanField(required=False, initial=False, label="Staff")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_active']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '')
        user.is_active = self.cleaned_data.get('is_active', True)
        user.is_staff = self.cleaned_data.get('is_staff', True)
        if commit:
            user.save()
        return user


class CustomUserChangeForm(UserChangeForm):
    password = None
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'is_superuser']
    






