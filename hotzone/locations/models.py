from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    userName = models.CharField(unique=True)
    chpStaffNumber = models.CharField(max_length=7, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    firstName = models.CharField()
    lastName = models.CharField()

    USERNAME_FIELD = 'userName'
    #REQUIRED_FIEDS = ['email', 'firstName', 'lastName', 'chpStaffNumber']

    def __str__(self):
        return self.userName

class Patient(models.Model):
    name = models.CharField(max_length=80, default="")
    idNumber = models.CharField(max_length=20)
    dateOfBirth = models.DateField()

    def __str__(self):
        return f'{self.id}  {self.name}'


class Virus(models.Model):
    name = models.CharField(max_length=30)
    commonName = models.CharField(max_length=50)
    maxInfectiousPeriod = models.CharField(max_length=3)

    def __str__(self):
        return self.name
    class Meta:
        verbose_name_plural='Viruses'


class Case(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    virus = models.ForeignKey(Virus, on_delete=models.CASCADE)
    dateConfirmed = models.DateField()
    caseType = models.CharField(max_length=8)

    def __str__(self):
        return f'{self.patient.name} {self.virus.name}'


class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=300)
    xCoord = models.FloatField()
    yCoord = models.FloatField()

    def __str__(self):
        return self.name


class Visit(models.Model):
    case = models.ForeignKey(Case, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    dateFrom = models.DateField()
    dateTo = models.DateField()
    category = models.CharField(max_length=20)

    def __str__(self):
        return f' {self.case.id} {self.location.place}'
        

#Old Code
'''
class Location(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=200)
    x = models.IntegerField(default=0)
    y= models.IntegerField(default=0)

    def __str__(self):
        return self.name
'''