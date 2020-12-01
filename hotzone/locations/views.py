from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout
from django.core import serializers

import requests
import datetime
import json
import math
import numpy as np
from sklearn.cluster import DBSCAN

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
                return render(request, 'error.html', {'message': message, 'back': True})
            
            # if location call successful, save data as session variable & render results
            else:
                locationsInDb, locationsNotInDb = split_data(data)
                request.session['dataindb'] = locationsInDb
                request.session['datanotindb'] = locationsNotInDb
                return render(request, 'location_results.html', {'dataindb': locationsInDb, 'datanotindb': locationsNotInDb})
            
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

def split_data(data):
    locationsInDb=[]
    locationsNotInDb=[]
    for i in data:
        check, l = check_location_in_DB(i)
        if(check==True):
            locationsInDb.append(i)
        else:
            locationsNotInDb.append(i)
    return locationsInDb, locationsNotInDb



def save_location(request):

    table = 0

    try:
        choice1 = request.POST.__getitem__('choice1')
    except Exception as e:
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        else:
            table = 1
                
    try:
        choice2 = request.POST.__getitem__('choice2')
    except Exception as e:
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        else:
            table = 0

    

    # Select information from session variable
    try:
        if(table==0):
            data = request.session['dataindb'][int(choice1)]
        else:
            data = request.session['datanotindb'][int(choice2)]   
    except Exception as e:
        print(e)


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

# To convert date to days
def convertDateToDays(d):
    #print("Date to Convert:", d)
    day = (d - datetime.date(2020,1,1)).days
    return day

# To convert days to date
def convertDaysToDate(d):
    ans = datetime.date(2020,1,1) + datetime.timedelta(days=d)
    return ans.strftime("%d/%m/%Y")

# clustering functions #1
def custom_metric(q, p, space_eps, time_eps):
    dist = 0
    for i in range(2):
        dist += (q[i] - p[i])**2
    spatial_dist = math.sqrt(dist)

    time_dist = math.sqrt((q[2]-p[2])**2)

    if time_dist/time_eps <= 1 and spatial_dist/space_eps <= 1 and p[3] != q[3]:
        return 1
    else:
        return 2

# clustering function #2
def cluster(vector_4d, distance, time, minimum_cluster):

    params = {"space_eps": distance, "time_eps": time}
    db = DBSCAN(eps=1, min_samples=minimum_cluster-1, metric=custom_metric, metric_params=params).fit_predict(vector_4d)
    output = {}

    unique_labels = set(db)
    total_clusters = len(unique_labels) if -1 not in unique_labels else len(unique_labels) -1

    print("Total clusters:", total_clusters)
    output["totalClustered"] = total_clusters

    total_noise = list(db).count(-1)

    print("Total un-clustered:", total_noise)
    output["totalUnclustered"] = total_noise

    for k in unique_labels:
        if k != -1:

            labels_k = db == k
            cluster_k = vector_4d[labels_k]

            print("Cluster", k, " size:", len(cluster_k))
            output[k] = []

            for pt in cluster_k:
                print("(x:{}, y:{}, date:{}, caseNo:{})".format(pt[0], pt[1], convertDaysToDate(pt[2]), pt[3]))
                output[k].append({
                    "x": pt[0],
                    "y": pt[1],
                    "date": convertDaysToDate(pt[2]),
                    "caseNo": pt[3]
                })

            print()
    return output

# View for clustering 
def clustering(request):

    # Since it gets annoying to keep re-entering values into the form,
    # I'm returning D, T & C as contexts so the form is auto-filled.
    # If it's a GET request, the default values are returned.
    # If it's a POST request, the values the user entered are returned. 
    # - Bevan

    # POST request => user submit input value of D, T, C from a html form
    if request.method == 'POST':
        # check if user is authenticated in POST method
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})

        # retreiving choices
        D = int(request.POST['D'])
        T = int(request.POST['T'])
        C = int(request.POST['C'])

        # data pre-processing...
        data = []
        visitData = Visit.objects.all()
        for visit in visitData:
            if visit.category=='Visit' and visit.dateFrom==visit.dateTo:
                X = visit.location.x
                Y = visit.location.y
                days = convertDateToDays(visit.dateFrom)
                caseNo = visit.case.pk
                data.append([X, Y, days, caseNo])
                #print(X, Y, days, caseNo)
        preparedData = np.array(data)
        #print(preparedData, D, T, C)

        # perform clustering .
        clustering_result = cluster(preparedData, D, T, C)
        
        # extract number of clusters
        clusters_num = int(clustering_result['totalClustered'])
        
        clusters = []
        # for each cluster
        for i in range(clusters_num):
            # for each record in a cluster
            for j in range(len(clustering_result[i])):
                # get the location name from db using x & y
                temp_location = Location.objects.filter(x=clustering_result[i][j]['x'], y=clustering_result[i][j]['y']).values('name')
                # print(temp_location)
                for loc in temp_location:
                    location_name = loc['name']
                # add the location into the data
                clustering_result[i][j]['location'] = location_name
            # separate cluster data separately
            clusters.append(clustering_result[i])
            
        print()
        print(clusters)
        print()

        return render(request, 'cluster.html', {'clusters': clusters, 'D': D, 'T': T, 'C': C})

    # GET request => user click the clustering button to input value of D, T, C
    else:
        # check if user is authenticated in GET method
        if not request.user.is_authenticated:
            return render(request, 'error.html', {'message': 'Please login to access this page!'})
        return render(request, 'cluster.html', {'D': 200, 'T': 3, 'C': 2})
        
