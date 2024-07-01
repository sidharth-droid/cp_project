from django.shortcuts import render
from rest_framework import generics,views,response,status
from .models import Complains,ScamPhone,ScamEmail,ScamLink,FIR
from .serializers import ComplainsSerializer,LinkSerializer,PhoneSerializer,EmailSerializer,FIRSerializer
import requests
from django.http import HttpResponse,HttpResponseRedirect,JsonResponse
from django.urls import reverse
from django.conf import settings
from django.contrib.auth import login as auth_login,logout,authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from .utils import invalidate_previous_sessions
from urllib.parse import unquote,urlparse
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.admin import UserAdmin,GroupAdmin
from django.contrib.auth.models import User,Group,update_last_login
from django.contrib.sessions.models import Session
from django.contrib import admin,messages
from .models import AdminActivity
from .admin import AdminActivityAdmin
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
import datetime,csv
from .forms import ComplainForm,AttachmentFormSet
import json
from openpyxl import Workbook
from io import BytesIO

class LoginView(views.APIView):
    def post(self,request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            current_session_key = request.session.session_key

            # Log out all other sessions for the same user
            Session.objects.filter(
                session_key__in=Session.objects.filter(
                    expire_date__gt=timezone.now()
                ).exclude(
                    session_key=current_session_key
                ).values_list('session_key', flat=True)
            ).delete()

            auth_login(request, user)
            update_last_login(None, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        else:
            return Response({'error': 'Invalid username or password'}, status=400)
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
    context = {
        'complains': complains,
        'is_superuser': request.user.is_superuser
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
    if data_type == "total_cases":
        data = Complains.objects.all()
    elif data_type == "closed_cases":
        data = Complains.objects.filter(status='closed')
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
    complains = Complains.objects.all()
    total_cases = Complains.objects.count()
    closed_cases = Complains.objects.filter(status='closed').count()
    current_date = datetime.datetime.now().date()
    registered_today = Complains.objects.filter(Date__date=current_date).count()
    
    last_week_dates = [(current_date - datetime.timedelta(days=i)) for i in range(30)]
    last_week_dates.reverse()
    daily_complaints = [
        Complains.objects.filter(Date__date=date).count() for date in last_week_dates
    ]
    chart_data = {
        'labels': [date.strftime('%Y-%m-%d') for date in last_week_dates],
        'data': daily_complaints
    }

    all_statuses = ['open', 'in review', 'visit ps', 'in progress', 'closed']

    status_counts = Complains.objects.values('status').annotate(count=Count('status'))
    status_dict = {status: 0 for status in all_statuses}

    total_cases = Complains.objects.count()
    for entry in status_counts:
        normalized_status = entry['status'].lower()
        if normalized_status in status_dict:
            status_dict[normalized_status] = entry['count']
    # status_percentages = {entry['status']: (entry['count'] / total_cases) * 100 for entry in status_counts}
    status_percentages = {status: (count / total_cases) * 100 for status, count in status_dict.items()}

    pie_chart_data = {
        'labels': list(status_percentages.keys()),
        'data': list(status_percentages.values())
    }


    
    
    # fraud_types_data = Complains.objects.values('fraud_type').annotate(count=Count('fraud_type'))
    # fraud_types = [{'fraud_type': item['fraud_type'], 'count': item['count']} for item in fraud_types_data]
    context = {
        'total_cases': total_cases,
        'closed_cases': closed_cases,
        'registered_today':registered_today,
        'complains':complains,
        'chart_data': chart_data,
        'pie_chart_data': pie_chart_data,
        # 'fraud_types': fraud_types,
        'is_superuser': request.user.is_superuser
    }
    return render(request, 'complainapp/admin_dashboard.html', context)
@login_required
@user_passes_test(is_super)
def user_list(request):
    user_admin=UserAdmin(User,admin.site)
    return user_admin.changelist_view(request)

@login_required
@user_passes_test(is_super)
def user_add(request):
    user_admin = UserAdmin(User, admin.site)
    return user_admin.add_view(request)

@login_required
@user_passes_test(is_super)
def user_change(request, object_id):
    user_admin = UserAdmin(User, admin.site)
    return user_admin.change_view(request, object_id)

@login_required
@user_passes_test(is_super)
def user_delete(request, object_id):
    user_admin = UserAdmin(User, admin.site)
    return user_admin.delete_view(request, object_id)

@login_required
@user_passes_test(is_super)
def group_list(request):
    group_admin = GroupAdmin(Group, admin.site)
    return group_admin.changelist_view(request)

@login_required
@user_passes_test(is_super)
def group_add(request):
    group_admin = GroupAdmin(Group, admin.site)
    return group_admin.add_view(request)

@login_required
@user_passes_test(is_super)
def group_change(request, object_id):
    group_admin = GroupAdmin(Group, admin.site)
    return group_admin.change_view(request, object_id)

@login_required
@user_passes_test(is_super)
def group_delete(request, object_id):
    group_admin = GroupAdmin(Group, admin.site)
    return group_admin.delete_view(request, object_id)

@login_required
@user_passes_test(is_super)
def login_activity(request):
    login_act = AdminActivityAdmin(AdminActivity,admin.site)
    return login_act.changelist_view(request)
    


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
