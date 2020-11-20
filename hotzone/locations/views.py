from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.core import serializers

import requests
import json

from django.views.generic import TemplateView

from .forms import LocationForm
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
<<<<<<< HEAD


=======
>>>>>>> parent of 61f2fde... Revert "add_visit partly done"

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
                    message = "Error 400: Bad Request" if code == 400 else "Error 500: Internal Server Error"
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
    chk=check_location_inDB(data)
    if(chk==True):
        return render(request, 'location_exists_indb.html')
    else:

        l = Location(name=data['nameEN'], address=data['addressEN'], x=data['x'], y=data['y'])

<<<<<<< HEAD
        try:
            l.save()
        except Exception as e:
            print(e)
=======
    try:
        l.save()
        request.session['location_pk'] = l.pk
    except Exception as e:
        print(e)
>>>>>>> parent of 61f2fde... Revert "add_visit partly done"

        return render(request, 'success.html')

def check_location_inDB(data):
    name=data['nameEN']
    address=data['addressEN']
    x=data['x']
    y=data['y']
    if(Location.objects.filter(name=name).exists()):
        v=Location.objects.filter(name=name)
        if(v.values()[0]['x']==x and v.values()[0]['y']==y and v.values()[0]['address']==address):
            return True
        else:
            return False
    else:
        return False

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
    try:
        choice = int(request.POST.__getitem__('choice'))
    except Exception as e:
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        else:
            return render(request, 'error.html', {'message': 'No case selected'})
    
    data_json = request.session['data']

    i = 0
    for obj in serializers.deserialize("json", data_json):
        if i == choice:
            pk = obj.object.pk
        else:
            i = i + 1

    data = Case.objects.filter(pk=pk)

    data_dict = json.loads(serializers.serialize("json", data))[0]
    request.session['case_pk'] = data_dict.get("pk")
    print(request.session['case_pk'])

    return render(request, 'view_case.html', {'data': data})

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


    v = Visit(case=Case.objects.get(pk=case_pk), location=Location.objects.get(pk=location_pk))
    # here saving must be fail as detail 
    try:
        v.save()
    except Exception as e:
        print(e)
    
    return render(request, 'add_visit.html')

