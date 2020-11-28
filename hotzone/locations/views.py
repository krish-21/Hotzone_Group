from django.http import HttpResponseRedirect
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

# View for Login Page
def login_view(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # extract data from request
        username = request.POST['username']
        password = request.POST['password']
        
        # Authenticate user using Django built-in function
        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse('index'))
        else:
            message = "Invalid Credentials!"
            return render(request, 'error.html', {'message': message})
    
    # if a GET (or any other method) we'll redirect to login page
    else:
        if not request.user.is_authenticated:
            return render(request, 'login.html')
        else:
            #redirect to home if user is authenticated and try to access login page again
            return HttpResponseRedirect(reverse('index'))


# View for Logout Page
def logout_view(request):
    logout(request)
    return render(request, 'logout.html')

# View for HomePage
class HomePage(TemplateView):
    template_name = "index.html"


# Helper function to make API Call and return status code & data
def get_location_api(name):
    # make the API Call
    r = requests.get('https://geodata.gov.hk/gs/api/v1.0.0/locationSearch?q=' + name)
    
    # check response code & handle it
    if r.status_code == 200:
        data = r.json()
        filtered = []
        for row in data:
            # Extract useful data
            filtered.append({key: row[key] for key in ['x', 'y', 'nameEN', 'addressEN']})
        return 200, filtered
    else:
        return r.status_code, None


# View for Seacrh Locations Page
def search_location(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':

        # check if user is authenticated in POST method
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        
        # create a form instance and populate it with data from the request:
        form = LocationForm(request.POST)
        
        # check whether it's valid:
        if form.is_valid():
            # extract name from form.cleaned_data
            name = form.cleaned_data['name']

            # Make the API call
            code, data = get_location_api(name)
                        
            # redirect to a new URL:
            # if no data returned, return GeoLocation Error
            if data == None:
                message = "Error 400: Bad Request. Please try again!" if code == 400 else "Error 500: Internal Server Error. Please try again!"
                return render(request, 'error.html', {'message': message})
            
            # if location call successful, save data as session variable & render results
            else:
                request.session['data'] = data
                return render(request, 'location_results.html', {'data': data})
            
    # if a GET (or any other method) we'll create a blank  Location Form
    else:
        # check if user is authenticated in GET method
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        else:
            # To guarantee user not breaking the logic if no case is selected before once logged in
            try:
                case_pk = request.session['case_pk']
            except Exception as e:
                return render(request, 'error.html', {'message': 'Insecure Action!'})
            
            # If user is authenticated, following the logic and selected a case before, action is permitted
            form = LocationForm()
            return render(request, 'search.html', {'form': form, 'case_pk' : case_pk})


# Helper function to check if a Location already exists in database
def check_location_in_DB(data):
    # Extract data from function argument
    name = data['nameEN']
    address = data['addressEN']
    x = data['x']
    y = data['y']

    # Search database by name
    if(Location.objects.filter(name=name).exists()):
        v = Location.objects.filter(name=name)
        # Check all other fields
        if(v.values()[0]['x']==x and v.values()[0]['y']==y and v.values()[0]['address']==address):
            return True, v.values_list('pk', flat=True)[0]
        else:
            return False, None
    else:
        return False, None


# View for Save Location Page
def save_location(request):
    # Extract information from request
    try:
        choice = request.POST.__getitem__('choice')
    except Exception as e:
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        else:
            return render(request, 'error.html', {'message': 'No location selected'})

    # Select information from session variable
    data = request.session['data'][int(choice)]
    
    # Query the existing Location database
    chk, location_pk = check_location_in_DB(data)

    # If location exists, save primary key of Location to session variable
    if(chk == True):
        request.session['location_pk'] = location_pk

    # Else, create Location object, save to database & save primary key to session variable
    else:
        l = Location(name=data['nameEN'], address=data['addressEN'], x=data['x'], y=data['y'])
        
        try:
            l.save()
            request.session['location_pk'] = l.pk
        except Exception as e:
            print("Exception: ")
            print(e)

    form = AddVisitForm()
    
    return render(request, 'add_visit.html', {'form': form, 'wasPresent': chk})


# View for List Locations Page
def list_locations(request):
    # check if user is authenticated in GET method
    if not request.user.is_authenticated:
        return render(request, 'error.html', {'message': 'Please login to access this page!'})
    else:
        # Query the database to get all locations
        data = Location.objects.order_by('name')

        # If data is empty
        if not data:
            return render(request, 'list_locations.html', {'data': data, 'empty': True})

        # Else
        return render(request, 'list_locations.html', {'data': data, 'empty': False})


# View for List Cases Page
def list_cases(request):
    # check if user is authenticated in GET method
    if not request.user.is_authenticated:
        return render(request, 'error.html', {'message': 'Please login to access this page!'})
    else:
        # Query the database to get all locations
        data = Case.objects.all()

        # If data is empty
        if not data:
            return render(request, 'list_cases.html', {'data': data, 'empty': True})
        
        # Else

        # Serialize data to json
        data_json = serializers.serialize('json', data)

        # Save data to session variable
        request.session['data'] = data_json
        
        return render(request, 'list_cases.html', {'data': data, 'empty': False})

def view_case(request):
    # if this is a POST request we need to process the form data
    if request.method=='POST':
        # check if user is authenticated in POST method
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})

        # Extract data from request
        try:
            choice = int(request.POST.__getitem__('choice'))
        except Exception as e:
            return render(request, 'error.html', {'message': 'No case selected'})

        # Get data from session variable
        data_json = request.session['data']

        # Extract primary key of selected case
        i = 0
        for obj in serializers.deserialize("json", data_json):
            if i == choice:
                pk = obj.object.pk
                break
            else:
                i = i + 1
    
    # if a GET (or any other method), use session variables for data
    else:
        # check if user is authenticated in GET method
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        try:
            # Get Location primary key from session variable
            pk = request.session['case_pk']
        except Exception as e:
            return render(request, 'error.html', {'message': 'No case selected'})
            
    # Query database for case & visit data
    caseData = Case.objects.filter(pk=pk)
    visitData = Visit.objects.filter(case=pk)

    # Save Location Primary Key to session variable
    request.session['case_pk'] = pk

    return render(request, 'view_case.html', {'caseData': caseData, 'visitData': visitData})


# View for Add Visit Page
def add_visit (request):
    if request.method == 'POST':
        # check if user is authenticated in POST method
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})

        # Get Case Primary Key from session variable
        try:
            case_pk = request.session['case_pk']
        except Exception as e:
            return render(request, 'error.html', {'message': 'No case selected'})

        # Get Location Primary Key from session variable
        try:
            location_pk = request.session['location_pk']
        except Exception as e:
            return render(request, 'error.html', {'message': 'No location selected'})

        print("case_pk: " + str(case_pk) + " location_pk: " + str(location_pk))

        # create a form instance and populate it with data from the request:
        form = AddVisitForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # extract visit data from form.cleaned_data
            v = Visit(
                case=Case.objects.get(pk=case_pk), 
                location=Location.objects.get(pk=location_pk),
                dateFrom=form.cleaned_data['datefrom'],
                dateTo=form.cleaned_data['dateto'],
                category=form.cleaned_data['category'])
            
            # Save Visit to database
            try:
                v.save()
            except Exception as e:
                return render(request, 'error.html', {'message': 'Cannot save visit'})

            caseData = Case.objects.filter(pk=case_pk)
            visitData = Visit.objects.filter(case=case_pk)

            return render(request, 'view_case.html', {'caseData': caseData, 'visitData': visitData, 'showMsg': True})

    # if a GET (or any other method) we'll create a blank Visit Form
    else:
        # check if user is authenticated in GET method
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        else:
            # To guarantee user not breaking the logic if no case is selected before once logged in
            return render(request, 'error.html', {'message': 'Insecure Action!'})

# View for clustering logic
def clustering(request):
    # POST request => user submit input value of D, T, C from a html form
    if request.method == 'POST':
        # check if user is authenticated in POST method
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})

        # retreiving result here, add default value in case no value is provided in the form
        D = request.POST['D'] or 200
        T = request.POST['T'] or 3
        C = request.POST['C'] or 2

        # print value in console for local test only
        print('distance: {}, time: {}, min_cluster: {}'.format(D, T, C))


        # data pre-processing...
        # clustering logic...
        # clustering list result ready...


        # need to return the clustering result
        # the context is for test only
        sample_clustering_result = {'location': 'testLocation', 'x': '55', 'y': '55', 'visit_date': '2020-01-01', 'result_no': '777'}
        return render(request, 'cluster.html', {'clustering_result': sample_clustering_result})

    # GET request => user click the clustering button to input value of D, T, C
    else:
        # check if user is authenticated in GET method
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        return render(request, 'cluster.html')
        
