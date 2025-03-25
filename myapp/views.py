from django.shortcuts import render
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import GenericAPIView
from .models import Payment,Message, Course, Assessment,User , Grade, Enrollment,Submission
from .serializers import PaymentSerializer,MessageSerializer,GradeSerializer,SubmissionSerializer, GroupSerializer, CourseSerializer, AssessmentSerializer,UserSerializer, EnrollmentSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view,permission_classes
from django.contrib.auth import authenticate ,login as django_login
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import make_password
from rest_framework.permissions import AllowAny ,DjangoModelPermissions ,IsAuthenticated
from django.contrib.auth.models import Group
from django.conf import settings
from rest_framework.views import APIView
from django.urls import reverse
from .models import Payment
from django.core.mail import send_mail ,EmailMessage
import os


# Create your views here.
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    if request.method == 'POST':
        email = request.data.get('email')
        password = request.data.get('password')

        # Authenticate the user
        user = authenticate(username=email, password=password)
        if user==None:
            return Response({"error": "Invalid credentials"}, status=400)
        else:
            # Generate a token for the authenticated user
            token,_= Token.objects.get_or_create(user=user)
            groups = Group.objects.filter(user=user)
            group_names = [group.name for group in groups]
            return Response({
                "token": token.key,
                "message": f"Welcome, {user.username}!",
                "groups":(group_names)
            })


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        password = request.data.get('password')
        hash_password = make_password(password)
        a = serializer.save()
        a.password = hash_password
        a.save()
        return Response('user created !')
    else:
        return Response(serializer.errors)


@api_view(['get'])
@permission_classes([AllowAny])
def group_listing (request):
    objs = Group.objects.all()
    serializer = GroupSerializer(objs , many=True)
    return Response(serializer.data)


class SendMail(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        # Extract data from the request
        subject = request.data.get('subject')
        message = request.data.get('message')
        recipient_email = request.data.get('recipient_email')
        document_path = request.data.get('document')  # Optional file path

        # Validate required fields
        if not subject or not message or not recipient_email:
            return Response(
                {"error": "Subject, message, and recipient email are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Create the email object
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.EMAIL_HOST_USER,
                to=[recipient_email],
            )

            # Attach file only if document_path is provided and valid
            if document_path:
                if os.path.exists(document_path):  # Validate file existence
                    email.attach_file(document_path)
                else:
                    return Response(
                        {"error": f"The file at path '{document_path}' does not exist."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Send the email
            email.send(fail_silently=False)

            return Response({"success": "Email sent successfully!"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to send email. Error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CourseApiView(GenericAPIView):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes =[IsAuthenticated , DjangoModelPermissions]
    search_fields = ['name','instructor_name','difficulty']

    def post(self,request):
        if not request.user.has_perm('myapp.add_course'):
            return Response({"error": "You do not have permission to create a course."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user= request.user)
            return Response(serializer.data)
        return Response(serializer.errors)

    def get(self,request):
        course_objs = self.get_queryset()
        serializer = self.serializer_class(course_objs , many= True)
        return Response(serializer.data)

    def put(self,request,pk=None):
        if not request.user.has_perm('myapp.change_course'):
            return Response({"error": "You do not have permission to update a course."}, status=status.HTTP_403_FORBIDDEN)
        try:
            course_obj = self.queryset.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Course object not found."})

        serializer = self.serializer_class(course_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self,request,pk=None):
        if not request.user.has_perm('myapp.delete_course'):
            return Response({"error": "You do not have permission to delete a course."}, status=status.HTTP_403_FORBIDDEN)
        try:
            course_obj = self.queryset.get(pk=pk)
        except Course.DoesNotExist:
            return Response({"error": "Course object not found."})
        course_obj.delete()
        return Response({"message": "Course removed successfully."})


class AssessmentApiView(GenericAPIView):
    queryset = Assessment.objects.all()
    serializer_class = AssessmentSerializer
    permission_classes=[IsAuthenticated , DjangoModelPermissions]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            assessment = serializer.save(user=request.user)

            # Send an email with limited details in the body
            email_body = f"""
            Description: {assessment.description}
            Course Name: {assessment.course_name}
            Submission Date: {assessment.submission_date}
            """
            user_email=request.user.email
            if not user_email:
                return Response({"error": "User email not found."}, status=status.HTTP_400_BAD_REQUEST)

            email = EmailMessage(
                subject=f"Assessment Created: {assessment.type}",
                body=email_body,
                from_email=settings.EMAIL_HOST_USER,
                to=[user_email],
            )
            if assessment.attachment:  # Check if there is an attachment
                email.attach_file(assessment.attachment.path)
            try:
                email.send()
            except Exception as e:
                return Response({"error": "Assessment created, but email failed to send.", "details": str(e)},
                                status=status.HTTP_201_CREATED)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self,request):
        assessment_objs = self.get_queryset()
        serializer = self.serializer_class(assessment_objs , many= True)
        return Response(serializer.data)

    def put(self, request, pk=None):
        try:
            assessment_obj = self.queryset.get(pk=pk)
        except Assessment.DoesNotExist:
            return Response({"error": "Assessment object not found."})

        serializer = self.serializer_class(assessment_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self, request, pk=None):
        try:
            assessment_obj = self.queryset.get(pk=pk)
        except Assessment.DoesNotExist:
            return Response({"error": "Assessment object not found."})

        assessment_obj.delete()
        return Response({"message": "Assessment deleted successfully."})

class UserApiView(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get(self,request):
        user_objs = self.get_queryset()
        serializer = self.serializer_class(user_objs , many= True)
        return Response(serializer.data)

class EnrollmentApiview(GenericAPIView):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes=[IsAuthenticated , DjangoModelPermissions]
    filterset_fields=['status','progress']

    def get(self,request):
        enrollment_objs = self.get_queryset()
        serializer = self.serializer_class(enrollment_objs , many= True)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            # Custom validation for course start and end dates
            course_start_date = serializer.validated_data.get('course_start_date')
            course_end_date = serializer.validated_data.get('course_end_date')

            if course_start_date >= course_end_date:
                return Response(
                    {"error": "Course start date must be earlier than the course end date."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Step 3: Save the enrollment with user association
            enrollment = serializer.save()

            # Step 4: Send email notification
            try:
                send_mail(
                    subject="Enrollment Confirmed",
                    message=f"Dear {enrollment.user.username},\n\nYou have successfully enrolled in our {enrollment.course.name} courses. Enjoy your learning journey!",
                    from_email=settings.EMAIL_HOST_USER,  # Defined in settings.py
                    recipient_list=[enrollment.user.email]  # User's email
                )
            except Exception as e:
                return Response(
                    {"error": "Enrollment successful, but failed to send email notification."},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Step 5: Return success response
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # Step 6: Handle validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, pk=None):
        try:
            enrollment_obj = self.queryset.get(pk=pk)
        except Enrollment.DoesNotExist:
            return Response({"error": "Enrollment object not found."})

        serializer = self.serializer_class(enrollment_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self, request, pk=None):
        try:
            enrollment_obj = self.queryset.get(pk=pk)
        except Enrollment.DoesNotExist:
            return Response({"error": "Enrollment object not found."})

        enrollment_obj.delete()
        return Response({"message": "Enrollment object deleted successfully."})


class SubmissionApiView(GenericAPIView):
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes=[IsAuthenticated , DjangoModelPermissions]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors)

    def get(self,request):
        submission_objs = self.get_queryset()
        serializer = self.serializer_class(submission_objs , many= True)
        return Response(serializer.data)

    def delete(self, request, pk=None):
        try:
            submission_obj = self.queryset.get(pk=pk)
        except Submission.DoesNotExist:
            return Response({"error": "Submission object not found."})

        submission_obj.delete()
        return Response({"message": "Submission object deleted successfully."})

class GradeApiView(GenericAPIView):
    queryset = Grade.objects.all()
    serializer_class = GradeSerializer
    permission_classes=[IsAuthenticated , DjangoModelPermissions]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data)
        return Response(serializer.errors)

    def get(self,request):
        grade_objs = self.get_queryset()
        serializer = self.serializer_class(grade_objs , many= True)
        return Response(serializer.data)

    def put(self, request, pk=None):
        try:
            grade_obj = self.queryset.get(pk=pk)
        except Grade.DoesNotExist:
            return Response({"error": "Grade object not found."})

        serializer = self.serializer_class(grade_obj, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self, request, pk=None):
        try:
            grade_obj = self.queryset.get(pk=pk)
        except Grade.DoesNotExist:
            return Response({"error": "Grade object not found."})

        grade_obj.delete()
        return Response({"message": "Grade object deleted successfully."})

class MessageApiView(GenericAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer

    def post(self,request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.dat )
        return Response(serializer.errors)



def payment_success(request):
    transaction_id = request.GET.get('pid')  # Get transaction reference ID
    amount = request.GET.get('amt')         # Get payment amount
    return render(request, 'payment_successfull.html', {
        'transaction_id': transaction_id,
        'amount': amount,
    })

def payment_failed(request):
    return render(request, 'payment_failed.html', {
        'message': 'Payment failed. Please try again.',
    })


class PaymentView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        """Initiate a Payment"""
        # Use PaymentSerializer to validate input data
        serializer = PaymentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Extract validated data
        user = request.user
        amount = serializer.validated_data['amount']
        course = serializer.validated_data['course']

        # Create a new payment record
        payment = Payment.objects.create(
            user=user,
            amount=amount,
            payment_status='pending'
        )
        payment.course.set(course)
        payment.save()
        # Generate the eSewa payment payload
        payload = {
            'amt': amount,
            'pdc': 0,
            'psc': 0,
            'txAmt': 0,
            'tAmt': amount,
            'pid': str(payment.id),
            'scd': settings.ESEWA_DEMO_MERCHANT_ID,
            'su': request.build_absolute_uri(reverse('payment_success')),
            'fu': request.build_absolute_uri(reverse('payment_failed')),
        }

        # Render the payment.html template with the payload
        return render(request, 'payment.html', {
            'payment_url': settings.ESEWA_DEMO_PAYMENT_URL,
            'payload': payload,
        })
    def get(self, request):
        """Verify a Payment"""
        ref_id = request.query_params.get('refId')
        payment_id = request.query_params.get('pid')
        amount = request.query_params.get('amt')

        try:
            payment = Payment.objects.get(id=payment_id)
            payload = {
                'amt': amount,
                'rid': ref_id,
                'pid': payment_id,
                'scd': settings.ESEWA_DEMO_MERCHANT_ID,
            }

            # Verify with eSewa
            import requests
            response = requests.post(settings.ESEWA_DEMO_VERIFY_URL, data=payload)
            if '<response_code>Success</response_code>' in response.text:
                payment.payment_status = 'completed'
                payment.ref_id = ref_id
                payment.save()
                return Response({'status': 'Payment verified successfully'})
            else:
                payment.payment_status = 'failed'
                payment.save()
                return Response({'status': 'Payment verification failed'}, status=400)

        except Payment.DoesNotExist:
            return Response({'error': 'Payment not found'}, status=404)



    def delete(self, request, *args, **kwargs):
        """Delete a Payment"""
        serializer = PaymentSerializer(data=request.data)  # Validate input
        serializer.is_valid(raise_exception=True)

        # Retrieve the payment object from the serializer
        payment = serializer.validated_data['payment_id']

        # Delete the payment
        payment.delete()

        return Response({'error': 'Payment deleted successfully'})