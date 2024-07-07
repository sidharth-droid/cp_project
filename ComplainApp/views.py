from django.shortcuts import render
from rest_framework import generics,views,response,status,permissions
from .models import Complains,ScamPhone,ScamEmail,ScamLink,FIR
from .serializers import ComplainsSerializer,LinkSerializer,PhoneSerializer,EmailSerializer,FIRSerializer
import requests
from django.http import HttpResponse,HttpResponseRedirect,JsonResponse
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import login as auth_login,logout,authenticate,update_session_auth_hash
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm,PasswordChangeForm
from .utils import invalidate_previous_sessions
from urllib.parse import unquote,urlparse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.db.models import Count,Q
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
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
import datetime,csv
from .forms import ComplainForm,AttachmentFormSet,CustomUserChangeForm,GroupForm,CustomUserCreationForm
import json
from openpyxl import Workbook
from io import BytesIO
from django.db.models.functions import TruncMonth,TruncYear,TruncWeek,Lower

def session_invalidated(request):
    if request.user.is_authenticated:
        logout(request)
    return render(request, 'complainapp/session_invalidated.html')
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

            # # Log out all other sessions for the same user
            # Session.objects.filter(
            #     session_key__in=Session.objects.filter(
            #         expire_date__gt=timezone.now()
            #     ).exclude(
            #         session_key=current_session_key
            #     ).values_list('session_key', flat=True)
            # ).delete()

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
class LinkDetail(generics.RetrieveAPIView):
    queryset = ScamLink.objects.all()
    serializer_class = LinkSerializer
    lookup_field = 'url'
    lookup_url_kwarg = 'url'
    def get_object(self):
        url_param = self.kwargs.get(self.lookup_url_kwarg)
        try:
            return ScamLink.objects.get(url=url_param)
        except ScamLink.DoesNotExist:
            pass

        normalized_url_param = self.normalize_url(url_param)
        for link in ScamLink.objects.all():
            normalized_db_url = self.normalize_url(link.url)
            print(normalized_db_url)
            if normalized_url_param == normalized_db_url:
                return link
        self.raise_not_found()

    def normalize_url(self, url):
        parsed_url = urlparse(url)
        domain = parsed_url.netloc or parsed_url.path
        return domain.lstrip('www.')

    def raise_not_found(self):
        from rest_framework.exceptions import NotFound
        raise NotFound(detail="Link not found", code=404)
    
class PhoneDetail(generics.RetrieveAPIView):
    queryset = ScamPhone.objects.all()
    serializer_class = PhoneSerializer
    lookup_field = 'number'
    lookup_url_kwarg = 'number'
class EmailDetail(generics.RetrieveAPIView):
    queryset = ScamEmail.objects.all()
    serializer_class = EmailSerializer
    lookup_field = 'email'
    lookup_url_kwarg = 'email'   
def AdminLogin(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_staff:
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


# class ComplainListView(ListView):
#     model = Complains
#     template_name = 'complainapp/view_complains.html'
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

    
    context = {
        'complains': complains,
        'is_superuser': request.user.is_superuser,
        'Complains': Complains,
        'status_choices': Complains._meta.get_field('status').choices,  
        'selected_status': status,
        'distinct_investigating_officers': distinct_investigating_officers,
        'distinct_fraud_types': distinct_fraud_types,
        'search_query': search_query


    }
    return render(request, 'complainapp/view_complains.html', context)
# class ComplainCreateView(CreateView):
#     model = Complains
#     form_class = ComplainForm
#     template_name = 'complainapp/add_complain.html'
#     success_url = reverse_lazy('add_complain')
#     def get_context_data(self, **kwargs):
#         data = super().get_context_data(**kwargs)
#         if self.request.POST:
#             data['attachments'] = AttachmentFormSet(self.request.POST, self.request.FILES)
#         else:
#             data['attachments'] = AttachmentFormSet()
#         return data

#     def form_valid(self, form):
#         context = self.get_context_data()
#         attachments = context['attachments']
#         if form.is_valid() and attachments.is_valid():
#             self.object = form.save()
#             attachments.instance = self.object
#             attachments.save()
#             return redirect(self.get_success_url())
#         else:
#             return self.form_invalid(form)
@login_required
def complain_create_view(request):
    if request.method == 'POST':
        form = ComplainForm(request.POST)
        attachments = AttachmentFormSet(request.POST, request.FILES)
        if form.is_valid() and attachments.is_valid():
            complain = form.save()
            attachments.instance = complain
            attachments.save()
            return redirect('add_complain')  # Adjust the success URL as needed
    else:
        form = ComplainForm()
        attachments = AttachmentFormSet()
    context = {
        'form': form,
        'attachments': attachments,
    }
    return render(request, 'complainapp/add_complain.html', context)

# class ComplainUpdateView(UpdateView):
#     model = Complains
#     form_class = ComplainForm
#     template_name = 'complainapp/edit_complain.html'
#     success_url = reverse_lazy('view_complains')
@login_required
def complain_update_view(request, pk):
    complain = get_object_or_404(Complains, pk=pk)
    if request.method == 'POST':
        form = ComplainForm(request.POST, instance=complain)
        if form.is_valid():
            form.save()
            return redirect('view_complains')  # Adjust the success URL as needed
    else:
        form = ComplainForm(instance=complain)
    context = {
        'form': form,
    }
    return render(request, 'complainapp/edit_complain.html', context)

# class ComplainDeleteView(DeleteView):
#     model = Complains
#     template_name = 'complainapp/delete_complain.html'
#     success_url = reverse_lazy('view_complains')
@login_required
def complain_delete_view(request, pk):
    complain = get_object_or_404(Complains, pk=pk)
    if request.method == 'POST':
        complain.delete()
        return redirect('view_complains')  # Adjust the success URL as needed
    context = {
        'complains': complain,
    }
    return render(request, 'complainapp/delete_complain.html', context)
def is_staff(user):
    return user.is_staff
def is_super(user):
    return user.is_superuser
# @login_required
# def get_chart_data(request):
#     time_range = request.GET.get('time_range', 'monthly')
#     start_date = request.GET.get('start_date')
#     end_date = request.GET.get('end_date')

#     # Default to current month
#     if not start_date or not end_date:
#         start_date = datetime.date.today().replace(day=1).strftime('%Y-%m-%d')
#         end_date = (datetime.date.today().replace(day=1) + datetime.timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d')

#     chart_data = calculate_chart_data(start_date, end_date)

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
    wb = Workbook()
    ws = wb.active
    ws.title = data_type

    headers = ["Ack Number", "Mobile Number", "Name", "Address", "Email", "Fraud Type", "Steps Taken", "Status", "Investigating Officer", "Date"]
    ws.append(headers)

    for complain in data:
        ws.append([
            complain.ack_number,
            complain.mobile_number,
            complain.name,
            complain.address,
            complain.email,
            complain.fraud_type,
            complain.steps_taken,
            complain.status,
            complain.investigating_officer,
            complain.Date.strftime('%Y-%m-%d %H:%M:%S')
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
def AdminDashboard(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    time_range = request.GET.get('time_range', 'monthly')

    if start_date and end_date:
        try:
            start_date_obj = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()
            complains = Complains.objects.filter(Date__date__gte=start_date_obj, Date__date__lte=end_date_obj)
            complains_closed = Complains.objects.filter(close_date__date__gte=start_date_obj, Date__date__lte=end_date_obj)
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

    # monthly_complaints = Complains.objects.annotate(period=period_annotation).values('period').annotate(count=Count('pk'))
    # closed_complaints = Complains.objects.filter(status='closed').annotate(period=close_period_annotation).values('period').annotate(count=Count('pk'))
    # chart_data = {
    #     'labels': [entry['period'].strftime('%Y-%m-%d') if time_range == 'weekly' else entry['period'].strftime('%Y-%m') if time_range == 'monthly' else entry['period'].strftime('%Y') for entry in monthly_complaints],
    #     'registered_data': [entry['count'] for entry in monthly_complaints],
    #     'closed_data': [entry['count'] for entry in closed_complaints if entry['period'] in [e['period'] for e in monthly_complaints]]
    # }
    # last_month_dates = [(current_date - datetime.timedelta(days=i)) for i in range(30)]
    # last_month_dates.reverse()

    # daily_registered_complaints = [
    #     Complains.objects.filter(Date__date=date).count() for date in last_month_dates
    # ]
    # daily_closed_complaints = [
    #     Complains.objects.filter(Date__date=date, status='closed').count() for date in last_month_dates
    # ]
    # chart_data = {
    #     'labels': [date.strftime('%Y-%m-%d') for date in last_month_dates],
    #     'registered_data': daily_registered_complaints,
    #     'closed_data': daily_closed_complaints
    # }

    all_statuses = ['open', 'in review', 'visit ps', 'in progress', 'closed']

    status_counts = Complains.objects.values('status').annotate(count=Count('status'))
    status_dict = {status: 0 for status in all_statuses}

    total_cases1 = Complains.objects.count()
    for entry in status_counts:
        normalized_status = entry['status'].lower()
        if normalized_status in status_dict:
            status_dict[normalized_status] = entry['count']
    # status_percentages = {entry['status']: (entry['count'] / total_cases) * 100 for entry in status_counts}
    status_percentages = {status: (count / total_cases1) * 100 for status, count in status_dict.items()}

    pie_chart_data = {
        'labels': list(status_percentages.keys()),
        'data': list(status_percentages.values())
    }
    designation = ""
    if is_super(request.user):
        designation = "Admin"
    elif is_staff(request.user):
        designation = "Staff"
    else:
        designation = "Member"

        
    
    
    # fraud_types_data = Complains.objects.values('fraud_type').annotate(count=Count('fraud_type'))
    # fraud_types = [{'fraud_type': item['fraud_type'], 'count': item['count']} for item in fraud_types_data]
    context = {
        'total_cases': total_cases,
        'closed_cases': closed_cases,
        'registered_today':registered_today,
        'pending_cases':pending_cases,
        'complains':complains,
        'chart_data': chart_data,
        'pie_chart_data': pie_chart_data,
        'start_date': start_date,  # Ensure the date is sent back to the template
        'end_date': end_date,
        'time_range': time_range,

        # 'fraud_types': fraud_types,
        'is_superuser': request.user.is_superuser,
        'username':request.user.username,
        'designation':designation
    }
    return render(request, 'complainapp/admin_dashboard.html', context)
# @login_required
# @user_passes_test(is_super)
# def user_list(request):
#     user_admin=UserAdmin(User,admin.site)
#     return user_admin.changelist_view(request)

# @login_required
# @user_passes_test(is_super)
# def user_add(request):
#     user_admin = UserAdmin(User, admin.site)
#     return user_admin.add_view(request)

# @login_required
# @user_passes_test(is_super)
# def user_change(request, object_id):
#     user_admin = UserAdmin(User, admin.site)
#     return user_admin.change_view(request, object_id)

# @login_required
# @user_passes_test(is_super)
# def user_delete(request, object_id):
#     user_admin = UserAdmin(User, admin.site)
#     return user_admin.delete_view(request, object_id)

# @login_required
# @user_passes_test(is_super)
# def group_list(request):
#     group_admin = GroupAdmin(Group, admin.site)
#     return group_admin.changelist_view(request)

# @login_required
# @user_passes_test(is_super)
# def group_add(request):
#     group_admin = GroupAdmin(Group, admin.site)
#     return group_admin.add_view(request)

# @login_required
# @user_passes_test(is_super)
# def group_change(request, object_id):
#     group_admin = GroupAdmin(Group, admin.site)
#     return group_admin.change_view(request, object_id)

# @login_required
# @user_passes_test(is_super)
# def group_delete(request, object_id):
#     group_admin = GroupAdmin(Group, admin.site)
#     return group_admin.delete_view(request, object_id)

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
    return render(request, 'complainapp/user_list.html', {'users': users,'is_superuser': request.user.is_superuser})
# View to create user
@login_required
@permission_required('auth.add_user', raise_exception=True)
def user_create_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)

            return redirect('user_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'complainapp/user_form.html', {'form': form})

# View to update user
@login_required
@permission_required('auth.change_user', raise_exception=True)
def user_update_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=user)
        password_form = PasswordChangeForm(user, request.POST)

        if form.is_valid() and password_form.is_valid():
            form.save()
            password_form.save()
            update_session_auth_hash(request, user)  # Keeps user logged in after password change
            messages.success(request, 'User information and password updated successfully.')
            return redirect('user_list')
    else:
        form = CustomUserChangeForm(instance=user)
        password_form = PasswordChangeForm(user)

    return render(request, 'complainapp/user_form.html', {
        'form': form,
        'password_form': password_form,
        'user': user
    })

# View to delete user
@login_required
@permission_required('auth.delete_user', raise_exception=True)
def user_delete_view(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('user_list')
    return render(request, 'complainapp/user_confirm_delete.html', {'user': user})

# View to list groups
@login_required
@permission_required('auth.view_group', raise_exception=True)
def group_list_view(request):
    groups = Group.objects.all()
    return render(request, 'complainapp/group_list.html', {'groups': groups})

# View to create group
@login_required
@permission_required('auth.add_group', raise_exception=True)
def group_create_view(request):
    if request.method == 'POST':
        form = GroupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('group_list')
    else:
        form = GroupForm()
    return render(request, 'complainapp/group_form.html', {'form': form})


# View to update group
@login_required
@permission_required('auth.change_group', raise_exception=True)
def group_update_view(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if request.method == 'POST':
        form = GroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            return redirect('group_list')
    else:
        form = GroupForm(instance=group)
    return render(request, 'complainapp/group_form.html', {'form': form})


# View to delete group
@login_required
@permission_required('auth.delete_group', raise_exception=True)
def group_delete_view(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if request.method == 'POST':
        group.delete()
        return redirect('group_list')
    return render(request, 'complainapp/group_confirm_delete.html', {'group': group})
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
    context = {
        'adminobj':adminobj,
        'is_superuser': request.user.is_superuser,
        'distinct_users':user_dict,
        'selected_user': user_id,
        'search_query':search_query

    }
    return render(request, 'complainapp/login_act.html', context)

    # login_act = AdminActivityAdmin(AdminActivity,admin.site)
    # return login_act.changelist_view(request)
    


def logout_handle(request):
    logout(request)
    messages.success(request,'You have been successfully logged out.')
    return redirect(reverse_lazy('admin_login'))








# @login_required
# @user_passes_test(is_staff)
# def view_complains(request):
#     complains = Complains.objects.all()
#     return render(request, 'complainapp/view_complains.html', {'complains': complains})

# @login_required
# @user_passes_test(is_staff)
# def add_complain(request):
#     if request.method == 'POST':
#         form = ComplainForm(request.POST)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Complain added successfully.")
#             return redirect('view_complains')
#         else:
#             messages.error(request, "There was an error adding the complain.")
#     else:
#         form = ComplainForm()
#     return render(request, 'complainapp/add_complain.html', {'form': form})

# @login_required
# @user_passes_test(is_staff)
# def edit_complain(request, complain_id):
#     complain = get_object_or_404(Complains, pk=complain_id)
#     if request.method == 'POST':
#         form = ComplainForm(request.POST, instance=complain)
#         if form.is_valid():
#             form.save()
#             messages.success(request, "Complain updated successfully.")
#             return redirect('view_complains')
#         else:
#             messages.error(request, "There was an error updating the complain.")
#     else:
#         form = ComplainForm(instance=complain)
#     return render(request, 'complainapp/edit_complain.html', {'form': form})

# @login_required
# @user_passes_test(is_staff)
# def delete_complain(request, complain_id):
#     complain = get_object_or_404(Complains, pk=complain_id)
#     complain.delete()
#     messages.success(request, "Complain deleted successfully.")
#     return redirect('view_complains')

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
    writer.writerow(['Date', 'ack_number', 'name', 'status', 'fraud_type'])  # Adjust headers as needed
    for complain in complains:
        writer.writerow([complain.Date, complain.ack_number, complain.name, complain.status, complain.fraud_type])

    return response

# def truecaller_bot_view(request):
#     if request.method == "POST":
#         message = request.POST.get("message")
#         if message:
#             bot_token = settings.TELEGRAM_BOT_TOKEN
#             chat_id = settings.TELEGRAM_CHAT_ID  # This should be customized
#             send_message_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

#             response = requests.post(send_message_url, data={
#                 'chat_id': chat_id,
#                 'text': message
#             })
            
#             if response.status_code == 200:
#                 # Message sent successfully
#                 pass

#         return HttpResponseRedirect(reverse('truecaller-bot'))

#     context = {
#         'bot_token': settings.TELEGRAM_BOT_TOKEN,
#         'chat_id': settings.TELEGRAM_CHAT_ID,
#     }
#     return render(request, 'admin/truecaller_bot.html', context)

# class LinkDetail(views.APIView):
#     def get(self, request, format=None):
#         url = request.query_params.get('url')
#         if not url:
#             return response.Response({'error': 'URL parameter is required'}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             link = ScamLink.objects.get(url=url)
#             serializer = LinkSerializer(link)
#             return response.Response(serializer.data)
#         except ScamLink.DoesNotExist:
#             return response.Response({'error': 'Link not found'}, status=status.HTTP_404_NOT_FOUND)
