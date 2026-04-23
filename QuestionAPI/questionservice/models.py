from django.db import models
from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.contrib.auth.models import AbstractUser, BaseUserManager

# class User(models.Model):
#     name = models.CharField(max_length=150)
#     email = models.EmailField(unique=True)
#     password = models.CharField(max_length=255)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return self.email

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)
    
class User(AbstractUser):
    username = None
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  

    objects = UserManager()

    def __str__(self):
        return self.email


class Board(models.Model):
    name = models.CharField(max_length=128, unique=True)

    def __str__(self): return self.name

class SchoolClass(models.Model):
    name = models.CharField(max_length=64)  # "Class 6", "Class 7"
    def __str__(self): return self.name

class Subject(models.Model):
    name = models.CharField(max_length=128)
    board = models.ForeignKey(Board, on_delete=models.RESTRICT, related_name='subjects')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.RESTRICT, related_name='subjects')

    class Meta:
        unique_together = ('name', 'board', 'school_class')

    def __str__(self): return f"{self.name} - {self.school_class} - {self.board}"

class Book(models.Model):
    title = models.CharField(max_length=256)
    author = models.CharField(max_length=128, blank=True, null=True)
    board = models.ForeignKey(Board, on_delete=models.RESTRICT, related_name='books')
    school_class = models.ForeignKey(SchoolClass, on_delete=models.RESTRICT, related_name='books')
    subject = models.ForeignKey(Subject, on_delete=models.RESTRICT, related_name='books')

    def __str__(self): return self.title

class Chapter(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chapters')
    chapter_number = models.PositiveIntegerField()
    name = models.CharField(max_length=256)

    class Meta:
        unique_together = ('book', 'chapter_number')
        ordering = ['chapter_number']

    def __str__(self): return f"{self.book.title} - {self.chapter_number}. {self.name}"

# Choices for question type & difficulty
QUESTION_TYPE_CHOICES = [
    ('mcq','MCQ'),
    ('true_false','True/False'),
    ('fill_blank','Fill in the blank'),
    ('short','Short answer'),
    ('long','Long answer'),
    ('match','Match the following'),
]

DIFFICULTY_CHOICES = [
    ('easy','Easy'),
    ('medium','Medium'),
    ('hard','Hard'),
]

class Question(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='questions')
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE, related_name='questions')
    subject = models.ForeignKey(Subject, on_delete=models.RESTRICT, related_name='questions')
    question_text = models.TextField()
    # options for MCQ or complex payload
    options = models.JSONField(blank=True, null=True)   # stored as JSONB in Postgres
    answer = models.JSONField(blank=True, null=True)    # supports single or multiple answers
    type = models.CharField(max_length=32, choices=QUESTION_TYPE_CHOICES)
    difficulty = models.CharField(max_length=16, choices=DIFFICULTY_CHOICES)
    marks = models.PositiveSmallIntegerField(default=1)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # For full-text search (optional) - maintained via triggers or manually
    search_vector = SearchVectorField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['subject','book','chapter','type','difficulty']),
            GinIndex(fields=['search_vector']),  # needs to be populated by triggers or migrations for search
        ]

    def __str__(self): return f"Q{self.pk}: {self.question_text[:60]}"

class Paper(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='papers')
    title = models.CharField(max_length=255)
    exam_name = models.CharField(max_length=255)

    school_class = models.ForeignKey(SchoolClass, on_delete=models.RESTRICT)
    subject = models.ForeignKey(Subject, on_delete=models.RESTRICT)
    board = models.ForeignKey(Board, on_delete=models.RESTRICT)

    max_marks = models.IntegerField()
    duration = models.IntegerField()  # minutes

    created_at = models.DateTimeField(auto_now_add=True)


class PaperSection(models.Model):
    paper = models.ForeignKey(Paper, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=255)
    order = models.IntegerField()

    class Meta:
        ordering = ['order']

class PaperQuestion(models.Model):  
    paper_section = models.ForeignKey(PaperSection, on_delete=models.CASCADE, related_name='paper_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    marks = models.IntegerField()  # override default marks if needed   
    order = models.IntegerField()

    class Meta:
        ordering = ['order']