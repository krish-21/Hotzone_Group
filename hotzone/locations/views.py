from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.core import serializers

import requests
import json

from django.views.generic import TemplateView

from .forms import LocationForm, AddVisitForm
from .models import Location, Case, Patient, Visit

# Create your views here.

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        else:
            message = "Invalid Credentials!"
            return render(request, 'error.html', {'message': message})
    else:
        return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return render(request, 'logout.html')


class HomePage(TemplateView):
    template_name = "index.html"

def get_location_api(name):
    # print(name)
    r = requests.get('https://geodata.gov.hk/gs/api/v1.0.0/locationSearch?q=' + name)
    # check response code & handle it
    if r.status_code == 200:
        data = r.json()
        filtered = []
        for row in data:
            filtered.append({key: row[key] for key in ['x', 'y', 'nameEN', 'addressEN']})
        return 200, filtered
    else:
        return r.status_code, None

def query_location(name):
    data = None
    #
    #
    #   Add code here
    #
    #
    return data

def search_location(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = LocationForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            name = form.cleaned_data['name']

            # Query the existing database for location
            data = query_location(name)

            # If no data returned, make the API call
            if data == None:
                code, data = get_location_api(name)
                            
                # redirect to a new URL:
                if data == None:
                    # if no data returned, return GeoLocation Error
                    message = "Error 400: Bad Request. Please try again!" if code == 400 else "Error 500: Internal Server Error. Please try again!"
                    return render(request, 'error.html', {'message': message})
                else:
                    # if location call successful, return results
                    request.session['data'] = data
                    return render(request, 'location_results.html', {'data': data})
            
            # location exists in the databse
            else:
                pass
                #
                #
                #   Add code here
                #
                #

    # if a GET (or any other method) we'll create a blank form
    else:
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        else:
            form = LocationForm()

    return render(request, 'search.html', {'form': form})

def save_location(request):
    try:
        choice = request.POST.__getitem__('choice')
    except Exception as e:
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        else:
            return render(request, 'error.html', {'message': 'No location selected'})

    data = request.session['data'][int(choice)]
    chk, location_pk =check_location_inDB(data)


    if(chk==True):
        request.session['location_pk'] = location_pk

    else:
        l = Location(name=data['nameEN'], address=data['addressEN'], x=data['x'], y=data['y'])

    try:
        l.save()
        request.session['location_pk'] = l.pk
    except Exception as e:
        print(e)

    form = AddVisitForm()
    return render(request, 'add_visit.html', {'form': form})

def check_location_inDB(data):
    name=data['nameEN']
    address=data['addressEN']
    x=data['x']
    y=data['y']
    if(Location.objects.filter(name=name).exists()):
        v=Location.objects.filter(name=name)
        if(v.values()[0]['x']==x and v.values()[0]['y']==y and v.values()[0]['address']==address):
            return True, v.values_list('pk', flat=True)[0]
        else:
            return False, None
    else:
        return False, None

def list_locations(request):
    data = Location.objects.order_by('name')

    template = loader.get_template('list_locations.html')
    context = {
        'data': data,
    }
    return HttpResponse(template.render(context, request))


def list_cases(request):
    data = Case.objects.all()
    
    data_json = serializers.serialize('json', data)

    request.session['data'] = data_json
    
    return render(request, 'list_cases.html', {'data': data})

def view_case(request):
    choice = -1
    try:
        if request.method=='POST':
            choice = int(request.POST.__getitem__('choice'))
        else: 
            pass
    except Exception as e:
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        else:
            return render(request, 'error.html', {'message': 'No case selected'})
    
    data_json = request.session['data']

    if choice!=-1:
        i = 0
        for obj in serializers.deserialize("json", data_json):
            if i == choice:
                pk = obj.object.pk
                break
            else:
                i = i + 1
    else:
        pk = request.session['case_pk']

    caseData = Case.objects.filter(pk=pk)
    visitData = Visit.objects.filter(case=pk)

    data_dict = json.loads(serializers.serialize("json", caseData))[0]
    request.session['case_pk'] = data_dict.get("pk")
    print(request.session['case_pk'])

    return render(request, 'view_case.html', {'caseData': caseData, 'visitData': visitData})

def add_visit (request):
    try:
        case_pk = request.session['case_pk']    
    except Exception as e:
        return render(request, 'error.html', {'message': 'No case selected'})

    try:
        location_pk = request.session['location_pk']    
    except Exception as e:
        return render(request, 'error.html', {'message': 'No location selected'})
    
    print("case_pk: " + str(case_pk) + " location_pk: " + str(location_pk))

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = AddVisitForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            v = Visit(
                case=Case.objects.get(pk=case_pk), 
                location=Location.objects.get(pk=location_pk),
                dateFrom=form.cleaned_data['datefrom'],
                dateTo=form.cleaned_data['dateto'],
                category=form.cleaned_data['category'])
            
            # here saving must be fail as detail 
            try:
                v.save()
            except Exception as e:
                return render(request, 'error.html', {'message': 'Cannot save visit'})

            return render(request, 'add_visit_success.html', {'case_pk': case_pk})

    else:
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        else:
            form = AddVisitForm()
        return render(request, 'add_visit.html', {'form': form})

