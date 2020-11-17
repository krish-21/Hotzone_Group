from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
# Register your models here.

from .models import Location, Patient, Virus, Case, Visit, StaffUser

class StaffUserAdmin(StaffUser):
    model = StaffUser

admin.site.register(StaffUser)
admin.site.register(Patient)
admin.site.register(Virus)
admin.site.register(Case)
admin.site.register(Location)
admin.site.register(Visit)