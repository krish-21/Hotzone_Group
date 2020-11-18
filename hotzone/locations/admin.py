from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import StuffUserCreationForm

# Register your models here.

from .models import Location, Patient, Virus, Case, Visit, StaffUser

class StaffUserAdmin(UserAdmin):
    model = StaffUser
    add_form = StuffUserCreationForm

    # for edit user form
    fieldsets = (
        *UserAdmin.fieldsets,
        (
            'CHP Stuff Number',
            {
                'fields': ('chpStaffNumber',)
            }
        )
    )

    # for add user form
    add_fieldsets = (
        *UserAdmin.add_fieldsets,
        (   
            None,
            {
                'fields': ('chpStaffNumber',)
            }
        )
    )
    


admin.site.register(StaffUser, StaffUserAdmin)
admin.site.register(Patient)
admin.site.register(Virus)
admin.site.register(Case)
admin.site.register(Location)
admin.site.register(Visit)