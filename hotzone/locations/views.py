from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.shortcuts import render
from django.urls import reverse
from django.contrib.auth import authenticate, login, logout

import requests

from django.views.generic import TemplateView

from .forms import LocationForm, SelectionForm
from .models import Location

# Create your views here.

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
   

def search_location(request):
    # if this is a POST request we need to process the form data
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = LocationForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            name = form.cleaned_data['name']
            code, data = get_location_api(name)
            
            # redirect to a new URL:
            if data == None:
                message = "Error 400: Bad Request" if code == 400 else "Error 500: Internal Server Error"
                return render(request, 'error.html', {'message': message})
            else:
                # return HttpResponseRedirect(reverse('index'))
                request.session['data'] = data
                return render(request, 'results.html', {'data': data})

    # if a GET (or any other method) we'll create a blank form
    else:
        form = LocationForm()

    return render(request, 'search.html', {'form': form})

def save_location(request):
    choice = request.POST.__getitem__('choice')
    data = request.session['data'][int(choice)]

    l = Location(name=data['nameEN'], address=data['addressEN'], x=data['x'], y=data['y'])

    try:
        l.save()
    except Exception as e:
        print(e)

    return render(request, 'success.html')


def list_locations(request):
    data = Location.objects.order_by('name')

    template = loader.get_template('list.html')
    context = {
        'data': data,
    }
    return HttpResponse(template.render(context, request))


def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        print("username="+username+" password="+password)
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
