from django.contrib import admin
from myapp.models import Course,Enrollment,Grade,Submission,Payment,Assessment,User ,Message

# Register your models here.


admin.site.register(User)
admin.site.register(Course )
admin.site.register(Enrollment)
admin.site.register(Payment)
admin.site.register(Assessment)
admin.site.register(Message)
admin.site.register(Submission)
admin.site.register(Grade)
