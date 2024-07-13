from django.shortcuts import render
from rest_framework import generics,views,response,status,permissions
from .models import Complains,FIR
from .serializers import ComplainsSerializer,FIRSerializer
import requests
from django.http import HttpResponse,HttpResponseRedirect,JsonResponse
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import login as auth_login,logout,authenticate,update_session_auth_hash,password_validation
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm,PasswordChangeForm
from .utils import invalidate_previous_sessions
from urllib.parse import unquote,urlparse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.db.models import Count,Q
from django.urls import reverse_lazy
from django.contrib.auth.admin import UserAdmin,GroupAdmin
from django.contrib.auth.models import User,Group,update_last_login
from django.contrib.sessions.models import Session
from django.contrib import admin,messages
from .models import AdminActivity,Profile
from .admin import AdminActivityAdmin
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
import datetime,csv,hashlib
from .forms import ComplainForm,CustomUserChangeForm,CustomUserCreationForm,FIRForm
from django.core.mail import send_mail
from .models import OTP
from .forms import OTPForm
import hashlib,os
import json
from openpyxl import Workbook
from io import BytesIO
from django.db.models.functions import TruncMonth,TruncYear,TruncWeek,Lower
from django import forms
from django.utils.translation import gettext as _
# from django_otp.decorators import otp_required
# from two_factor.forms import AuthenticationTokenForm, BackupTokenForm

def session_invalidated(request):
    if request.user.is_authenticated:
        logout(request)
    return render(request, 'ComplainApp/session_invalidated.html')

class LoginView(views.APIView):
    def post(self,request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if not request.session.session_key:
                request.session.create()
            current_session_key = request.session.session_key
            self.invalidate_other_sessions(user, current_session_key)
            auth_login(request, user)
            update_last_login(None, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        else:
            return Response({'error': 'Invalid username or password'}, status=400)
    def invalidate_other_sessions(self,user,current_session_key):
        all_sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in all_sessions:
            session_data = session.get_decode()
            if session.session_key != current_session_key and session_data.get('_auth_user_id')== str(user.id):
                session.delete()

#Serializers Api Class
class FIRList(generics.ListAPIView):
    queryset = FIR.objects.all()
    serializer_class = FIRSerializer
class FIRDetail(generics.RetrieveAPIView):
    queryset = FIR.objects.all()
    serializer_class = FIRSerializer
class ComplainsList(generics.ListAPIView):
    queryset = Complains.objects.all()
    serializer_class = ComplainsSerializer
class ComplaintDetail(generics.RetrieveAPIView):
    queryset = Complains.objects.all()
    serializer_class = ComplainsSerializer
class ComplainsCreate(generics.CreateAPIView):
    queryset = Complains.objects.all()
    serializer_class = ComplainsSerializer
    def perform_create(self, serializer):
        complaint = serializer.save()
        self.ack_number = complaint.ack_number
   
def AdminLogin(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                auth_login(request, user)
                # invalidate_previous_sessions(user)
                # return redirect('admin_dashboard')
                return redirect('send_otp')
            elif user.is_staff and not user.is_superuser:
                auth_login(request, user)
                invalidate_previous_sessions(user)
                return redirect('admin_dashboard')

                # return redirect('two_factor:login')
            else:
                messages.error(request, "You are not authorized to access the admin panel.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'ComplainApp/admin_login.html', {'form': form})

@login_required
def complain_list_view(request):
    complains = Complains.objects.all()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + timezone.timedelta(days=1)
        complains = complains.filter(Date__range=[start_date, end_date])

    # Filter by status
    status = request.GET.get('status')
    distinct_investigating_officers = Complains.objects.annotate(
        lower_officer=Lower('investigating_officer')
    ).values('lower_officer').distinct().values_list('lower_officer', flat=True)

    distinct_fraud_types = Complains.objects.annotate(
        lower_fraud_type=Lower('fraud_type')
    ).values('lower_fraud_type').distinct().values_list('lower_fraud_type', flat=True)
    if status:
        complains = complains.filter(status=status)
        print(status)

    # Filter by investigating officer
    investigating_officer = request.GET.get('investigating_officer')
    if investigating_officer:
        complains = complains.filter(investigating_officer__icontains=investigating_officer)

    # Filter by fraud type
    fraud_type = request.GET.get('fraud_type')
    if fraud_type:
        complains = complains.filter(fraud_type__icontains=fraud_type)
    
    search_query = request.GET.get('search', '')

    if search_query:
        search_query = search_query.strip()
        complains = Complains.objects.filter(
            Q(name__icontains=search_query) |
            Q(mobile_number__icontains=search_query) |
            Q(ack_number__icontains=search_query) |
            Q(fraud_type__icontains=search_query) |
            Q(investigating_officer__icontains=search_query)
        )
    complains = complains.order_by('-Date')
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"
    context = {
        'complains': complains,
        'is_superuser': request.user.is_superuser,
        'Complains': Complains,
        'status_choices': Complains._meta.get_field('status').choices,  
        'selected_status': status,
        'distinct_investigating_officers': distinct_investigating_officers,
        'distinct_fraud_types': distinct_fraud_types,
        'search_query': search_query,
        'username':request.user.username,
        'designation':designation
    }
    return render(request, 'ComplainApp/view_complains.html', context)

@login_required
def complain_create_view(request):
    if request.method == 'POST':
        form = ComplainForm(request.POST)
        if form.is_valid():
            complain = form.save()
            messages.success(request, f'Your complaint has been successfully submitted. Your acknowledgment number is {complain.ack_number}.')
            return redirect('add_complain')
        else:
            # print("Form is not valid. Errors:", form.errors)
            messages.error(request, 'There were some issues with your submission.')

    else:
        form = ComplainForm()
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"
    context = {
        'form': form,
        # 'errors':form.errors,
        # 'attachments': attachments,
        'is_superuser': request.user.is_superuser,
        'username':request.user.username,
        'designation':designation

    }
    return render(request, 'ComplainApp/add_complain.html', context)


@login_required
def complain_update_view(request, pk):
    complain = get_object_or_404(Complains, pk=pk)
    if request.method == 'POST':
        form = ComplainForm(request.POST, instance=complain)
        if form.is_valid():
            instance = form.save(commit=False)
            if instance.status == 'closed':
                instance.close_date = timezone.now()
            instance.save()
            # form.save()
            
            # messages.success(request, f'Your complaint has been successfully updated.')
            return redirect('view_complains')  # Adjust the success URL as needed
        else:
            messages.error(request, 'There were some issues with your submission.')

    else:
        form = ComplainForm(instance=complain)
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"
    context = {
        'form': form,
        'is_superuser': request.user.is_superuser,
        'username':request.user.username,
        'complaint': complain,
        'designation':designation
    }
    return render(request, 'ComplainApp/edit_complain.html', context)

@login_required
def complain_delete_view(request, pk):
    complain = get_object_or_404(Complains, pk=pk)
    if request.method == 'DELETE':
        complain.delete()
        return JsonResponse({'message': 'Complain deleted successfully.'}, status=204)
    else:
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
   
def is_staff(user):
    return user.is_staff
def is_super(user):
    return user.is_superuser

@login_required
def fir_list_view(request):
    firs = FIR.objects.all()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    if start_date and end_date:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + timezone.timedelta(days=1)
        firs = firs.filter(Date__range=[start_date, end_date])

    # Filter by status
    # status = request.GET.get('status')
    distinct_investigating_officers = Complains.objects.annotate(
        lower_officer=Lower('investigating_officer')
    ).values('lower_officer').distinct().values_list('lower_officer', flat=True)

    distinct_fraud_types = Complains.objects.annotate(
        lower_fraud_type=Lower('fraud_type')
    ).values('lower_fraud_type').distinct().values_list('lower_fraud_type', flat=True)
    # if status:
    #     complains = complains.filter(status=status)
    #     print(status)

    # Filter by investigating officer
    investigating_officer = request.GET.get('investigating_officer')
    if investigating_officer:
        firs = firs.filter(complain__investigating_officer__icontains=investigating_officer)

    # Filter by fraud type
    fraud_type = request.GET.get('fraud_type')
    if fraud_type:
        firs = firs.filter(complain__fraud_type__icontains=fraud_type)
    
    search_query = request.GET.get('search', '')

    if search_query:
        search_query = search_query.strip()
        firs = FIR.objects.filter(
            Q(complain__name__icontains=search_query) |
            Q(complain__mobile_number__icontains=search_query) |
            Q(complain__ack_number__icontains=search_query) |
            Q(complain__fraud_type__icontains=search_query) |
            Q(complain__investigating_officer__icontains=search_query)|
            Q(name_of_complainant__icontains=search_query)|
            Q(name_of_accused__icontains=search_query)|
            Q(fir_number__icontains=search_query)
        )
    firs = firs.order_by('-Date')
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"
    context = {
        'firs': firs,
        'is_superuser': request.user.is_superuser,
        'Complains': Complains,
        # 'status_choices': Complains._meta.get_field('status').choices,  
        # 'selected_status': status,
        'distinct_investigating_officers': distinct_investigating_officers,
        'distinct_fraud_types': distinct_fraud_types,
        'search_query': search_query,
        'username':request.user.username,
        'designation':designation


    }
    return render(request, 'ComplainApp/view_fir.html', context)
@login_required
def fir_create_view(request):
    if request.method == 'POST':
        form = FIRForm(request.POST)
        if form.is_valid():
            fir = form.save()
            messages.success(request,f'FIR {fir.fir_number} has been successfully created for the complain with acknowledgment number {fir.complain.ack_number}.')
            return redirect('add_fir')
        # else:
            # messages.error(request, 'There were some issues with your submission.')
            

    else:
        form = FIRForm()
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"
    context = {
        'form': form,
        'is_superuser': request.user.is_superuser,
        'username':request.user.username,
        'designation':designation

    }
    return render(request, 'ComplainApp/add_fir.html', context)

@login_required
def fir_update_view(request, pk):
    fir = get_object_or_404(FIR, pk=pk)
    if request.method == 'POST':
        form = FIRForm(request.POST, instance=fir)
        if form.is_valid():
            form.save()
            # messages.success(request, f'Your complaint has been successfully updated.')
            return redirect('view_fir')  # Adjust the success URL as needed
        else:
            messages.error(request, 'There were some issues with your submission.')

    else:
        form = FIRForm(instance=fir)
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"
    context = {
        'form': form,
        'is_superuser': request.user.is_superuser,
        'username':request.user.username,
        'fir': fir,
        'designation':designation
    }
    return render(request, 'ComplainApp/edit_fir.html', context)

@login_required
def fir_delete_view(request, pk):
    fir = get_object_or_404(FIR, pk=pk)
    if request.method == 'DELETE':
        fir.delete()
        return JsonResponse({'message': 'FIR deleted successfully.'}, status=204)
    else:
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
    

@login_required
def get_pie_chart_data(request, time_range):
    if time_range == 'lastYear':
        start_date = datetime.datetime.now() - datetime.timedelta(days=365)
    elif time_range == 'lastTwoYears':
        start_date = datetime.datetime.now() - datetime.timedelta(days=730)
    elif time_range == 'lastSixMonths':
        start_date = datetime.datetime.now() - datetime.timedelta(days=182)
    else:
        start_date = None

    if start_date:
        complaints = Complains.objects.filter(Date__gte=start_date)
    else:
        complaints = Complains.objects.all()

    data = complaints.values('status').annotate(count=Count('status'))
    labels = [entry['status'] for entry in data]
    counts = [entry['count'] for entry in data]

    return JsonResponse({
        'labels': labels,
        'data': counts
    })


@login_required
@user_passes_test(is_super)
def send_otp(request):
    otp = OTP.objects.create(user=request.user)
    raw_otp = otp.generate_otp()
    send_mail(
        'Your OTP Code',
        f'Your OTP code is {raw_otp}',
        'commissioneratepolice@gmail.com',
        [request.user.email],
        fail_silently=False,

    )
    # return render(request, 'ComplainApp/otp_sent.html')
    return redirect('verify_otp')

@login_required
@user_passes_test(is_super)
def verify_otp(request):
    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp_code = form.cleaned_data['otp']
            try:
                hashed_otp = hashlib.sha256(otp_code.encode()).hexdigest()
                otp = OTP.objects.get(user=request.user, otp_code=hashed_otp, is_active=True)
                if otp.is_valid():
                    otp.is_active = False
                    otp.save()
                    request.session['otp_verified'] = True
                    invalidate_previous_sessions(request.user)
                    return redirect('admin_dashboard')
                else:
                    form.add_error('otp', 'OTP has expired or is invalid.')
            except OTP.DoesNotExist:
                form.add_error('otp', 'Invalid OTP')
    else:
        form = OTPForm()
    try:
        otp = OTP.objects.get(user=request.user, is_active=True)
        time_to_expiry = otp.calculate_time_to_expiry() 
        print("time",time_to_expiry)
        otp_expiry_time = int(time_to_expiry.total_seconds() / 60)
    except OTP.DoesNotExist:
        otp_expiry_time = None
    print(otp_expiry_time)
    return render(request, 'ComplainApp/verify_otp.html', {'form': form,'otp_expiry_time': otp_expiry_time})
@login_required
@user_passes_test(is_super)
def resend_otp(request):
    try:
        otp = OTP.objects.filter(user=request.user, is_active=True).update(is_active=False)
    except OTP.DoesNotExist:
        pass
    
    
    new_otp = OTP.objects.create(user=request.user)
    raw_otp = new_otp.generate_otp()
    
    send_mail(
        'Your New OTP Code',
        f'Your new OTP code is {raw_otp}',
        os.environ.get('SEND_EMAIL_USER'),
        [request.user.email],
        fail_silently=False,
    )
    
    # messages.success(request, 'New OTP has been sent to your email.')
    return redirect('verify_otp')
@login_required
@user_passes_test(is_staff)

def AdminDashboard(request):
    if not request.session.get('otp_verified') and request.user.is_superuser:
        return redirect('verify_otp')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    time_range = request.GET.get('time_range', 'monthly')

    if start_date and end_date:
        try:
            start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            complains = Complains.objects.filter(Date__date__gte=start_date_obj, Date__date__lte=end_date_obj)
            complains_closed = Complains.objects.filter(close_date__date__gte=start_date_obj, close_date__date__lte=end_date_obj)
            total_cases = complains.count()
            closed_cases = complains_closed.count()

        except ValueError:
            complains = Complains.objects.all()
            complains_closed = complains
            total_cases = Complains.objects.count()
            start_date = None
            end_date = None
    else:
        complains = Complains.objects.all()
        complains_closed = complains
        total_cases = Complains.objects.count()
        start_date = None
        end_date = None
    

    total_cases = complains.count()
    closed_cases = complains_closed.filter(status='closed').count()
    pending_cases = Complains.objects.all().count() - Complains.objects.filter(status='closed').count()
    current_date = datetime.datetime.now().date()
    registered_today = Complains.objects.filter(Date__date=current_date).count()
    if time_range == 'weekly':
        weekly_complaints = Complains.objects.annotate(week=TruncWeek('Date')).values('week').annotate(count=Count('pk'))
        chart_data = {
            'labels': [entry['week'].strftime('%Y-%m-%d') for entry in weekly_complaints],
            'registered_data': [entry['count'] for entry in weekly_complaints],
            'closed_data': [Complains.objects.filter(close_date__week=entry['week'].isocalendar()[1], status='closed').count() for entry in weekly_complaints]
        }
    elif time_range == 'yearly':
        # Get the yearly data
        yearly_complaints = Complains.objects.annotate(year=TruncYear('Date')).values('year').annotate(count=Count('pk'))
        chart_data = {
            'labels': [entry['year'].strftime('%Y') for entry in yearly_complaints],
            'registered_data': [entry['count'] for entry in yearly_complaints],
            'closed_data': [Complains.objects.filter(close_date__year=entry['year'].year, status='closed').count() for entry in yearly_complaints]
        }
    else:
        # Get the monthly data (default)
        monthly_complaints = Complains.objects.annotate(month=TruncMonth('Date')).values('month').annotate(count=Count('pk'))
        chart_data = {
            'labels': [entry['month'].strftime('%Y-%m') for entry in monthly_complaints],
            'registered_data': [entry['count'] for entry in monthly_complaints],
            'closed_data': [Complains.objects.filter(close_date__month=entry['month'].month, status='closed').count() for entry in monthly_complaints]
        }

    all_statuses = ['open', 'in review', 'visit ps', 'in progress', 'closed']

    status_counts = Complains.objects.values('status').annotate(count=Count('status'))
    status_dict = {status: 0 for status in all_statuses}

    total_cases1 = Complains.objects.count()
    for entry in status_counts:
        normalized_status = entry['status'].lower()
        if normalized_status in status_dict:
            status_dict[normalized_status] = entry['count']
    # status_percentages = {entry['status']: (entry['count'] / total_cases) * 100 for entry in status_counts}
    # status_percentages = {status: (count / total_cases1) * 100 for status, count in status_dict.items()}

    # pie_chart_data = {
    #     'labels': list(status_percentages.keys()),
    #     'data': list(status_percentages.values())
    # }
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"

        
    complains1 = complains.order_by('-Date')
    
    # fraud_types_data = Complains.objects.values('fraud_type').annotate(count=Count('fraud_type'))
    # fraud_types = [{'fraud_type': item['fraud_type'], 'count': item['count']} for item in fraud_types_data]
    context = {
        'total_cases': total_cases,
        'closed_cases': closed_cases,
        'registered_today':registered_today,
        'pending_cases':pending_cases,
        'complains':complains,
        'complains1':complains1,
        'chart_data': chart_data,
        # 'pie_chart_data': pie_chart_data,
        'start_date': start_date,  # Ensure the date is sent back to the template
        'end_date': end_date,
        'time_range': time_range,

        # 'fraud_types': fraud_types,
        'is_superuser': request.user.is_superuser,
        'username':request.user.username,
        'designation':designation
    }
    return render(request, 'ComplainApp/admin_dashboard.html', context)


@login_required
@permission_required('auth.view_user', raise_exception=True)
def user_list_view(request):
    search_query = request.GET.get('search', '')
    if search_query:
        users = User.objects.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    else:
        users = User.objects.all()
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"
    return render(request, 'ComplainApp/user_list.html', {'users': users,'is_superuser': request.user.is_superuser,'username':request.user.username,
        'designation': designation})
# View to create user
@login_required
@permission_required('auth.add_user', raise_exception=True)
def user_create_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Profile.objects.create(user=user)

            return redirect('user_list')
    else:
        form = CustomUserCreationForm()
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"
    return render(request, 'ComplainApp/user_form.html', {'form': form,'is_superuser': request.user.is_superuser,'username':request.user.username,
        'designation': designation})

# View to update user
@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_update_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        password_form = CustomPasswordChangeForm(user, request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, 'User information updated successfully.')
            return redirect('user_list')
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)  # Keeps user logged in after password change
            messages.success(request, 'Password updated successfully.')
            return redirect('user_list')
    else:
        form = CustomUserChangeForm(instance=user)
        password_form = CustomPasswordChangeForm(user)
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"
    return render(request, 'ComplainApp/user_update.html', {
        'form': form,
        'password_form': password_form,
        'user': user,'is_superuser': request.user.is_superuser,
        'username':request.user.username,
        'designation': designation
    })

class CustomPasswordChangeForm(PasswordChangeForm):
    error_messages = {
        'password_incorrect': _("Your old password was entered incorrectly. Please enter it again."),
        'password_mismatch': _("The two password fields didn't match."),
    }

    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True}),
    )
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Password'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'placeholder': 'Confirm Password'}),
    )

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                self.error_messages['password_incorrect'],
                code='password_incorrect',
            )
        return old_password

    def clean_new_password2(self):
        new_password1 = self.cleaned_data.get('new_password1')
        new_password2 = self.cleaned_data.get('new_password2')
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise forms.ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        return new_password2
# View to delete user
@login_required
@permission_required('auth.delete_user', raise_exception=True)
def user_delete_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'DELETE':
        user.delete()
        return JsonResponse({'message': 'User deleted successfully.'}, status=204)
    else:
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

@login_required
@user_passes_test(is_super)
def login_activity(request):
    adminobj = AdminActivity.objects.all()
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date and end_date:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d') + timezone.timedelta(days=1)
        adminobj = adminobj.filter(login_time__range=[start_date, end_date])
    
    distinct_user_ids = AdminActivity.objects.values_list('user__id', flat=True).distinct()
    distinct_users = User.objects.filter(id__in=distinct_user_ids).values('id','username').distinct()
    user_dict = {user['id']: user['username'] for user in distinct_users}
    user_id = request.GET.get('user')
    if user_id:
        adminobj = adminobj.filter(user__id=user_id)
    search_query = request.GET.get('search', '')

    if search_query:
        search_query = search_query.strip()
        adminobj = AdminActivity.objects.filter(
            Q(user__username__icontains=search_query) |
            Q(ip_address__icontains=search_query))
    adminobj = adminobj.order_by('-login_time')
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"
    context = {
        'adminobj':adminobj,
        'is_superuser': request.user.is_superuser,
        'distinct_users':user_dict,
        'selected_user': user_id,
        'search_query':search_query,
        'username':request.user.username,
        'designation': designation

    }
    return render(request, 'ComplainApp/login_act.html', context)
    
@login_required
@user_passes_test(is_super)
def delete_login_activity(request, activity_id):
    if request.method == "DELETE":
        activity = get_object_or_404(AdminActivity, pk=activity_id)
        activity.delete()
        return JsonResponse({'message': 'User deleted successfully.'}, status=204)
    else:
        return JsonResponse({'error': 'Method not allowed.'}, status=405)

def logout_handle(request):
    logout(request)
    messages.success(request,'You have been successfully logged out.')
    return redirect(reverse_lazy('admin_login'))

@login_required
@user_passes_test(is_staff)
def download_report(request, days):
    end_date = timezone.now()
    start_date = end_date - timezone.timedelta(days=int(days))
    
    # Filter complains based on date range
    complains = Complains.objects.filter(Date__range=(start_date, end_date))

    # Create CSV file
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="report_{days}_days.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'ack_number', 'name', 'status', 'fraud_type'])  
    for complain in complains:
        writer.writerow([complain.Date, complain.ack_number, complain.name, complain.status, complain.fraud_type])

    return response

@login_required
@user_passes_test(is_staff)
def download_excel(request, data_type):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    data = Complains.objects.all()

    if start_date and end_date:
        try:
            start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            date_filtered_data = data.filter(Date__date__gte=start_date_obj, Date__date__lte=end_date_obj)
            date_filtered_data_closed = data.filter(close_date__date__gte=start_date_obj, close_date__date__lte=end_date_obj)
            
            print("Working")
        except ValueError:
            date_filtered_data = Complains.objects.all()
            date_filtered_data_closed = Complains.objects.filter(status='closed')
            print("Not Working")

    else:
        date_filtered_data = Complains.objects.all()
        date_filtered_data_closed = Complains.objects.filter(status='closed')

    if data_type == "total_cases":
        data = date_filtered_data
    elif data_type == "closed_cases":
        data = date_filtered_data_closed.filter(status='closed')
    elif data_type == "registered_today":
        today = datetime.date.today()
        data = Complains.objects.filter(Date__date=today)
    elif data_type == "pending":
        data = Complains.objects.exclude(status='closed')
    wb = Workbook()
    ws = wb.active
    ws.title = data_type

    headers = ["Ack Number", "Mobile Number", "Name", "Address", "Email", "Fraud Type", "Description","Accused Account Numbers","Accused Suspicious Items","Steps Taken", "Status", "Investigating Officer", "Files","Date"]
    ws.append(headers)

    for complain in data:
        ws.append([
            complain.ack_number,
            complain.mobile_number,
            complain.name,
            complain.address,
            complain.email,
            complain.fraud_type,
            complain.description,
            complain.accusedAccountNumbers,
            complain.accusedSuspiciousItem,
            complain.steps_taken,
            complain.status,
            complain.investigating_officer,
            complain.files,
            complain.Date.strftime('%Y-%m-%d %H:%M:%S'),
        ])

    # Save the workbook to a BytesIO object
    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    # Send the file to the client
    response = HttpResponse(file_stream, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename={data_type}.xlsx'
    return response

@login_required
@user_passes_test(is_staff)
def download_fir(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    investigating_officer = request.GET.get('investigating_officer')
    fraud_type = request.GET.get('fraud_type')
    search_query = request.GET.get('search')
    
    firs = FIR.objects.all()

    if start_date and end_date:
        try:
            start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            firs = firs.filter(Date__date__gte=start_date_obj, Date__date__lte=end_date_obj)
            
            print("Working")
        except ValueError:
            firs = FIR.objects.all()
            print("Not Working")
        # firs = firs.filter(Date__range=[start_date, end_date])
    if investigating_officer:
        firs = firs.filter(complain__investigating_officer__icontains=investigating_officer)
    if fraud_type:
        firs = firs.filter(complain__fraud_type__icontains=fraud_type)
    if search_query:
        firs = firs.filter(
            Q(complain__name__icontains=search_query) |
            Q(complain__mobile_number__icontains=search_query) |
            Q(complain__ack_number__icontains=search_query) |
            Q(complain__fraud_type__icontains=search_query) |
            Q(complain__investigating_officer__icontains=search_query)|
            Q(name_of_complainant__icontains=search_query)|
            Q(name_of_accused__icontains=search_query)|
            Q(fir_number__icontains=search_query)
        )

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="firs.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'FIR Number', 'Date Reported',
        'Place of Occurrence', 'Distance', 'Direction', 'Date of Dispatch from PS',
        'Name of Complainant', 'Residence of Complainant', 'Name of Accused',
        'Residence of Accused', 'Description', 'Section', 'Steps Taken by IO', 'Result of the Case'
    ])


    for fir in firs:
        writer.writerow([
            fir.Date, f"'{fir.fir_number}", fir.date_reported,
            fir.place_of_occurrence, fir.distance, fir.direction, fir.date_of_dispatch_from_ps,
            fir.name_of_complainant, fir.residence_of_complainant, fir.name_of_accused,
            fir.residence_of_accused, fir.description, fir.section, fir.steps_taken_by_io, fir.result_of_the_case
        ])
    return response






