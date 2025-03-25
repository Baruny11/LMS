from django.urls import path
from .views import login,register,group_listing,CourseApiView,AssessmentApiView,UserApiView ,EnrollmentApiview
from .views import SendMail,SubmissionApiView,MessageApiView ,payment_failed,payment_success,GradeApiView  ,PaymentView
urlpatterns = [
    path('login/', login),
    path('register/',register),
    path('roles/',group_listing),
    path('api/send/mail/',SendMail.as_view()) ,
    path('course/', CourseApiView.as_view(), name='course'),
    path('course/<int:pk>/', CourseApiView.as_view(), name='course'),
    path('user/', UserApiView.as_view(), name = 'user'),
    path('assessment/', AssessmentApiView.as_view(), name='assessment'),
    path('assessment/<int:pk>/', AssessmentApiView.as_view(), name='assessment'),
    path('enrollment/',EnrollmentApiview.as_view(), name='enrollment'),
    path('enrollment/<int:pk>/',EnrollmentApiview.as_view(), name='enrollment'),
    path('submission/',SubmissionApiView.as_view(),name='submission'),
    path('grading/',GradeApiView.as_view(),name='grading'),
    path('payment/', PaymentView.as_view(), name='payment'),
    path('payment-success/', payment_success, name='payment_success'),
    path('payment-failed/', payment_failed, name='payment_failed'),
    path('message/',MessageApiView.as_view() , name = 'message'),
]
