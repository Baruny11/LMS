from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.models import Group
import uuid

# Custom User Model
class User(AbstractUser ):
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(unique=True)
    phone_no = models.IntegerField(null=True)
    address = models.CharField(max_length=200, null=True)
    username = models.CharField(max_length=50 , null=True)
    groups = models.ManyToManyField(Group)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username','phone_no', 'address']

class Course(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100  )
    description = models.TextField()
    user = models.ForeignKey(User ,on_delete=models.CASCADE ,null=True)

    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('advanced', 'Advanced'),
    ]
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES ,null=True)
    duration = models.CharField(max_length=50)
    fee = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Assessment(models.Model):
    id = models.AutoField(primary_key=True)
    description = models.TextField()
    submission_date = models.DateTimeField()
    course_id = models.ManyToManyField(Course)
    user = models.ForeignKey(User, on_delete=models.CASCADE ,null=True)
    course_name = models.CharField(max_length=100 ,null=True)
    attachment = models.FileField(upload_to='enrollment_attachments/', null=True)

    ASSESSMENT_TYPE_CHOICES = [
        ('quiz', 'Quiz'),
        ('assignment', 'Assignment'),
        ('project', 'Project'),
    ]
    type = models.CharField(max_length=20, choices=ASSESSMENT_TYPE_CHOICES)

class Enrollment(models.Model):
    enrollment_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ManyToManyField(Course)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    course_start_date = models.DateTimeField()
    course_end_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('graduated', 'Graduated')]
    )
    progress = models.FloatField(null=True)

    funds = models.DecimalField(max_digits=10, decimal_places=2 ,null=True)
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('partial', 'Partial'),
        ('cleared', 'Cleared'),
    ]
    payments_status = models.CharField(max_length=20,choices=PAYMENT_STATUS_CHOICES ,null=True)

class Submission(models.Model):
    submission_id = models.AutoField(primary_key=True)
    submission_assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    submission_date = models.DateField(auto_now_add=True)  # Automatically set the date when created
    submission_student = models.ForeignKey(User, on_delete=models.CASCADE)
    submission_file = models.FileField(upload_to='submission_files/', null=True)

class Grade(models.Model):
    grade_id = models.AutoField(primary_key=True)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)  # Changed to reference the Submission model directly
    grade_score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(100.0)])

class Message(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE ,null=True)
    content = models.TextField()  # The main text of the message
    timestamp = models.DateTimeField(auto_now_add=True)  # Automatically set when the message is created
    attached_file = models.FileField(upload_to='message_attachments/', null=True, blank=True)  # Tracks whether the recipient has read the message


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE )
    course = models.ManyToManyField(Course)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES)



    def __str__(self):
        return f"Payment {self.id} - {self.user} - {self.payment_status}"
