from django.shortcuts import render
from rest_framework import generics,views
from .models import Complains,FIR
from .serializers import ComplainsSerializer
import requests
from django.http import HttpResponse,JsonResponse
from django.contrib.auth import login as auth_login,logout,authenticate,update_session_auth_hash,password_validation
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm,PasswordChangeForm
from .utils import invalidate_previous_sessions
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.db.models import Count,Q
from django.urls import reverse_lazy
from django.contrib.auth.models import User,update_last_login
from django.contrib.sessions.models import Session
from django.contrib import messages
from .models import AdminActivity
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework.authtoken.models import Token
import datetime,csv,hashlib
from .forms import ComplainForm,CustomUserChangeForm,CustomUserCreationForm,FIRForm
from django.core.mail import send_mail,EmailMessage
from .models import OTP
from .forms import OTPForm
import hashlib,os
import json
from openpyxl import Workbook
from io import BytesIO
from django.db.models.functions import TruncMonth,TruncYear,TruncWeek,Lower
from django import forms
from django.utils.translation import gettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .mixins import CheckAllowedOriginMixin

# Helper function to check staff and superuser
def is_staff(user):
    return user.is_staff
def is_super(user):
    return user.is_superuser


@csrf_exempt
@require_POST
def delete_file_view(request):
    import json
    data = json.loads(request.body)
    file_url = data.get('file_url')
    complain_id = data.get('complain_id')
    
    if not file_url or not complain_id:
        return JsonResponse({'success': False, 'message': 'Invalid request.'})

    complain = get_object_or_404(Complains, pk=complain_id)

    if file_url in complain.files:
        complain.files.remove(file_url)
        complain.save()
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False, 'message': 'File not found.'})
    

# API For Compliant details
class ComplaintDetail(generics.RetrieveUpdateAPIView):
    queryset = Complains.objects.all()
    serializer_class = ComplainsSerializer
    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs['context'] = self.get_serializer_context()
        
        if self.request.method in ['PUT', 'PATCH']:
            serializer = serializer_class(*args, **kwargs)
            for field_name, field in serializer.fields.items():
                if field_name != 'files':
                    field.read_only = True
            return serializer

        return serializer_class(*args, **kwargs)
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        if 'files' not in request.data:
            raise ValidationError({"error": "Only 'files' field can be updated."})
        
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        if 'files' in request.data:
            instance.upload_status = False
            instance.save()

        return Response(serializer.data)


# API to create new Complaint/Register New Complaint
class ComplainsCreate(generics.CreateAPIView):
    queryset = Complains.objects.all()
    serializer_class = ComplainsSerializer
    def perform_create(self, serializer):
        complaint = serializer.save()
        self.ack_number = complaint.ack_number


# View to Handle Admin Login
def AdminLogin(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                auth_login(request, user)
                return redirect('send_otp')
            elif user.is_staff and not user.is_superuser:
                auth_login(request, user)
                invalidate_previous_sessions(user)
                return redirect('admin_dashboard')

            else:
                messages.error(request, "You are not authorized to access the admin panel.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'ComplainApp/admin_login.html', {'form': form})


# Send OTP to Email of User
@login_required
@user_passes_test(is_super)
def send_otp(request):
    otp = OTP.objects.create(user=request.user)
    raw_otp = otp.generate_otp()
    send_method = request.POST.get('send_method')

    email = EmailMessage(
                            subject='OTP to Login to Admin Panel',
                            body=f'Your OTP code is {raw_otp}',
                            from_email='scamscamq@gmail.com',
                            to=[request.user.email],
                            headers={'From': 'Commissionerate Of Police Orissa commissioneratepolice@nic.in<commissioneratepolice@gmail.com>'}
                        )
    email.send(fail_silently=False)
    
    return redirect('verify_otp')


# Verify OTP 
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


# Resend OTP
@login_required
@user_passes_test(is_super)
def resend_otp(request):
    try:
        otp = OTP.objects.filter(user=request.user, is_active=True).update(is_active=False)
    except OTP.DoesNotExist:
        pass
    
    
    new_otp = OTP.objects.create(user=request.user)
    raw_otp = new_otp.generate_otp()
    email = EmailMessage(subject='OTP to Login to Admin Panel',
                            body=f'Your New OTP code is {raw_otp}',
                            from_email='scamscamq@gmail.com',
                            to=[request.user.email],
                            headers={'From': 'Commissionerate Of Police Orissa commissioneratepolice@nic.in<commissioneratepolice@gmail.com>'}
                        )
    email.send(fail_silently=False)
    # send_mail(
    #     'Your New OTP Code',
    #     f'Your new OTP code is {raw_otp}',
    #     os.environ.get('SEND_EMAIL_USER'),
    #     [request.user.email],
    #     fail_silently=False,
    # )
    
    # messages.success(request, 'New OTP has been sent to your email.')
    return redirect('verify_otp')


# View to handle Admin Dashboard
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
    
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"

        
    complains1 = complains.order_by('-Date')
    
    context = {
        'total_cases': total_cases,
        'closed_cases': closed_cases,
        'registered_today':registered_today,
        'pending_cases':pending_cases,
        'complains':complains,
        'complains1':complains1,
        'chart_data': chart_data,
        'start_date': start_date,
        'end_date': end_date,
        'time_range': time_range,
        'is_superuser': request.user.is_superuser,
        'username':request.user.username,
        'designation':designation
    }
    return render(request, 'ComplainApp/admin_dashboard.html', context)


# View to show & handle complaints list
@login_required
@user_passes_test(is_staff)
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
    distinct_enquiry_officers = Complains.objects.annotate(
        lower_officer=Lower('enquiry_officer')
    ).values('lower_officer').distinct().values_list('lower_officer', flat=True)

    distinct_fraud_types = Complains.objects.annotate(
        lower_fraud_type=Lower('fraud_type')
    ).values('lower_fraud_type').distinct().values_list('lower_fraud_type', flat=True)
    if status:
        complains = complains.filter(status=status)
        print(status)

    # Filter by enquiry officer
    enquiry_officer = request.GET.get('enquiry_officer')
    if enquiry_officer:
        complains = complains.filter(enquiry_officer__icontains=enquiry_officer)

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
            Q(enquiry_officer__icontains=search_query)|
            Q(suspect_account_numbers__icontains=search_query)|
            Q(suspect_emails__icontains=search_query)|
            Q(suspect_links__icontains=search_query)|
            Q(suspect_mobile_numbers__icontains=search_query)|
            Q(address__icontains=search_query)|
            Q(place_of_incidence__icontains=search_query)|
            Q(email__icontains=search_query)
        )
    complains = complains.order_by('-Date')
    all_status = Complains._meta.get_field('status').choices + [('Verification Pending','Verification Pending')]
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
        'status_choices': all_status,  
        'selected_status': status,
        'distinct_enquiry_officers': distinct_enquiry_officers,
        'distinct_fraud_types': distinct_fraud_types,
        'search_query': search_query,
        'username':request.user.username,
        'designation':designation
    }
    return render(request, 'ComplainApp/view_complains.html', context)


# View to handle new complaint registration
@login_required
@user_passes_test(is_staff)
def complain_create_view(request):
    if request.method == 'POST':
        form = ComplainForm(request.POST)
        if form.is_valid():
            complain = form.save(commit=False)
            if complain.status == 'closed':
                complain.close_date = timezone.now()
            complain.save()
            file_urls = request.POST.get('file_urls')
            if file_urls:
                complain.files = json.loads(file_urls)
                complain.save()
            if complain.email:
                email = EmailMessage(
                            subject='Complaint Registration Confirmation',
                            body=f'''
                            Hello {complain.name},<br><br>
                            Your complaint has been successfully registered. Please keep your Acknowledgement Number <strong>{complain.ack_number}</strong> for future reference.<br><br>
                            To check the status of your complaint, visit <strong><a href="https://onlinecomplain.subrat.xyz/">www.cybercrimereporting.in</a></strong> .<br><br>
                            Thank you,<br>
                            Commissionerate of Police Orissa
                            ''',
                            from_email='commissioneratepolice@gmail.com',
                            to=[complain.email],
                            headers={'From': 'Commissionerate Of Police Orissa commissioneratepolice@nic.in<commissioneratepolice@gmail.com>'}
                        )
                email.content_subtype = "html"
                email.send(fail_silently=False)
            suspicious_items = []
            if complain.suspect_emails:
                suspicious_items.append(complain.suspect_emails)
            if complain.suspect_links:
                suspicious_items.append(complain.suspect_links)
            if complain.suspect_mobile_numbers:
                suspicious_items.append(complain.suspect_mobile_numbers)
            if complain.suspect_account_numbers:
                suspicious_items.append(complain.suspect_account_numbers)
            suspicious_items = ','.join(filter(None, suspicious_items))
            api_data = {
                "suspiciousItem": suspicious_items,
                "name": complain.name,
                "mobile_number": complain.mobile_number,
                "address": complain.address,
                "fraud_type": complain.description
            }
            api_data = json.dumps(api_data)
            print(api_data)
            try:
                response = requests.post('https://backendcp.subrat.xyz/v1/api/enquire/save', data=api_data,headers={'Content-Type': 'application/json'})
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                print("Issue with submitting to API: ",e)
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
        'is_superuser': request.user.is_superuser,
        'username':request.user.username,
        'designation':designation

    }
    return render(request, 'ComplainApp/add_complain.html', context)


# View to handle updation of complaints
@login_required
@user_passes_test(is_staff)
def complain_update_view(request, pk):
    complain = get_object_or_404(Complains, pk=pk)
    old_message = complain.message
    if request.method == 'POST':
        form = ComplainForm(request.POST, instance=complain)
        if form.is_valid():
            instance = form.save(commit=False)
            if instance.status == 'closed':
                instance.close_date = timezone.now()
            new_message = form.cleaned_data.get('message')
            if old_message != new_message:
                if instance.email:
                    email = EmailMessage(
                            subject='Notification Regarding Your Complaint',
                            body=f'There has been a message or update for your case with Acknowledgement Number {instance.ack_number}. Please check your complaint on the site for more details.',
                            from_email='commissioneratepolice@gmail.com',
                            to=[instance.email],
                            headers={'From': 'Commissionerate Of Police Orissa commissioneratepolice@nic.in<commissioneratepolice@gmail.com>'}
                        )
                    email.send(fail_silently=False)
            
            file_urls = request.POST.get('file_urls')
            if file_urls:
                new_files = json.loads(file_urls)
                instance.files = instance.files+new_files
                instance.save()
            instance.save()
           
            return redirect('view_complains')
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


# View to handle complaints deletion
@login_required
@user_passes_test(is_staff)
def complain_delete_view(request, pk):
    complain = get_object_or_404(Complains, pk=pk)
    if request.method == 'DELETE':
        complain.delete()
        return JsonResponse({'message': 'Complain deleted successfully.'}, status=204)
    else:
        return JsonResponse({'error': 'Method not allowed.'}, status=405)
   

# View to handle listing of FIRs
@login_required
@user_passes_test(is_staff)
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
    distinct_enquiry_officers = Complains.objects.annotate(
        lower_officer=Lower('enquiry_officer')
    ).values('lower_officer').distinct().values_list('lower_officer', flat=True)

    distinct_fraud_types = Complains.objects.annotate(
        lower_fraud_type=Lower('fraud_type')
    ).values('lower_fraud_type').distinct().values_list('lower_fraud_type', flat=True)
    # if status:
    #     complains = complains.filter(status=status)
    #     print(status)

    # Filter by enquiry officer
    enquiry_officer = request.GET.get('enquiry_officer')
    if enquiry_officer:
        firs = firs.filter(complain__enquiry_officer__icontains=enquiry_officer)

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
            Q(complain__status__icontains=search_query) |
            Q(complain__enquiry_officer__icontains=search_query)|
            Q(name_of_complainant__icontains=search_query)|
            Q(name_of_accused__icontains=search_query)|
            Q(place_of_occurrence__icontains=search_query)|
            Q(fir_number__icontains=search_query)
        ).distinct()
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
        'distinct_enquiry_officers': distinct_enquiry_officers,
        'distinct_fraud_types': distinct_fraud_types,
        'search_query': search_query,
        'username':request.user.username,
        'designation':designation


    }
    return render(request, 'ComplainApp/view_fir.html', context)


# View to handle FIR creation
@login_required
@user_passes_test(is_staff)
def fir_create_view(request):
    if request.method == 'POST':
        form = FIRForm(request.POST)
        if form.is_valid():
            fir = form.save()
            complain_ack_numbers = ", ".join([complain.ack_number for complain in fir.complain.all()])
            messages.success(request, f'FIR {fir.fir_number} has been successfully created for the complain(s) with acknowledgment number(s) {complain_ack_numbers}.')
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


# View to handle FIRs Updation
@login_required
@user_passes_test(is_staff)
def fir_update_view(request, pk):
    fir = get_object_or_404(FIR, pk=pk)
    if request.method == 'POST':
        form = FIRForm(request.POST, instance=fir)
        if form.is_valid():
            form.save()
            # messages.success(request, f'Your complaint has been successfully updated.')
            return redirect('view_fir')
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


# View to handle FIR deletion
@login_required
@user_passes_test(is_staff)
def fir_delete_view(request, pk):
    fir = get_object_or_404(FIR, pk=pk)
    if request.method == 'DELETE':
        fir.delete()
        return JsonResponse({'message': 'FIR deleted successfully.'}, status=204)
    else:
        return JsonResponse({'error': 'Method not allowed.'}, status=405)


# View to handle listing of Users
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


# View to list login activity
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
    

# View to delete login activity
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


# Download excel of complaints
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

    headers = ["Ack Number", "Mobile Number", "Name", "Address", "Email", "Place of Incidence","Fraud Type", "Description","Suspect Account Numbers","Suspect Emails","Suspect Links","Suspect Phone Numbers","Fraudlent Amount(INR)","Amount Recovered(INR)","Steps Taken", "Status", "Enquiry Officer","Date"]
    ws.append(headers)

    for complain in data:
        ws.append([
            complain.ack_number,
            complain.mobile_number,
            complain.name,
            complain.address,
            complain.email,
            complain.place_of_incidence,
            complain.fraud_type,
            complain.description,
            complain.suspect_account_numbers,
            complain.suspect_emails,
            complain.suspect_links,
            complain.suspect_mobile_numbers,
            complain.fraudlent_amount,
            complain.amount_recovered,
            complain.steps_taken,
            complain.status,
            complain.enquiry_officer,
            # complain.files,
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


# Download FIRs
@login_required
@user_passes_test(is_staff)
def download_fir(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    enquiry_officer = request.GET.get('enquiry_officer')
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
    if enquiry_officer:
        firs = firs.filter(complain__enquiry_officer__icontains=enquiry_officer)
    if fraud_type:
        firs = firs.filter(complain__fraud_type__icontains=fraud_type)
    if search_query:
        firs = firs.filter(
            Q(complain__name__icontains=search_query) |
            Q(complain__mobile_number__icontains=search_query) |
            Q(complain__ack_number__icontains=search_query) |
            Q(complain__fraud_type__icontains=search_query) |
            Q(complain__enquiry_officer__icontains=search_query)|
            Q(name_of_complainant__icontains=search_query)|
            Q(name_of_accused__icontains=search_query)|
            Q(fir_number__icontains=search_query)
        ).distinct()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="firs.csv"'
    writer = csv.writer(response)
    writer.writerow([
        'Date', 'FIR Number', 'Date Reported',
        'Place of Occurrence', 'Distance', 'Direction', 'Date of Dispatch from PS',
        'Name of Complainant', 'Residence of Complainant', 'Name of Accused',
        'Residence of Accused', 'Description', 'Section', 'Steps Taken Regarding Investigation', 'Result of the Case'
    ])


    for fir in firs:
        writer.writerow([
            fir.Date, f"'{fir.fir_number}", fir.date_reported,
            fir.place_of_occurrence, fir.distance, fir.direction, fir.date_of_dispatch_from_ps,
            fir.name_of_complainant, fir.residence_of_complainant, fir.name_of_accused,
            fir.residence_of_accused, fir.description, fir.section, fir.steps_taken_by_io, fir.result_of_the_case
        ])
    return response

