from rest_framework import serializers
from .models import Board, SchoolClass, Subject, Book, Chapter, Question, User, Paper, PaperQuestion, PaperSection
from django.contrib.auth.hashers import make_password, check_password

# class SignupSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'name', 'email', 'password', 'created_at', 'updated_at']
#         extra_kwargs = {
#             'password': {'write_only': True}
#         }

#     def create(self, validated_data):
#         validated_data['password'] = make_password(validated_data['password'])
#         return super().create(validated_data)
from django.contrib.auth import get_user_model

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "name", "password"]

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

# class LoginSerializer(serializers.Serializer):
#     email = serializers.EmailField()
#     password = serializers.CharField()

#     def validate(self, data):
#         try:
#             user = User.objects.get(email=data['email'])
#         except User.DoesNotExist:
#             raise serializers.ValidationError("Invalid email or password")

#         if not check_password(data['password'], user.password):
#             raise serializers.ValidationError("Invalid email or password")

#         return user
from django.contrib.auth import authenticate
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        request = self.context.get("request")

        user = authenticate(
            request=request,
            email=data["email"],
            password=data["password"],
        )

        if user is None:
            raise serializers.ValidationError("Invalid email or password")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")

        return user

class BoardSerializer(serializers.ModelSerializer):
    class Meta: model = Board; fields = ['id','name']

class SchoolClassSerializer(serializers.ModelSerializer):
    class Meta: model = SchoolClass; fields = ['id','name']

class SubjectSerializer(serializers.ModelSerializer):
    board = BoardSerializer(read_only=True)
    school_class = SchoolClassSerializer(read_only=True)
    class Meta: model = Subject; fields = ['id','name','board','school_class']

class BookSerializer(serializers.ModelSerializer):
    class Meta: model = Book; fields = ['id','title','author','board','school_class','subject']

class ChapterSerializer(serializers.ModelSerializer):
    class Meta: model = Chapter; fields = ['id','book','chapter_number','name']

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id','book','chapter','subject','question_text','options','answer','type','difficulty','marks','created_at']
        read_only_fields = ['created_at']

# For bulk create
class QuestionBulkSerializer(serializers.ListSerializer):
    child = QuestionSerializer()
    def create(self, validated_data):
        objs = [Question(**item) for item in validated_data]
        return Question.objects.bulk_create(objs)


class PaperListSerializer(serializers.ModelSerializer):
    school_class = serializers.CharField(source="school_class.name")
    subject = serializers.CharField(source="subject.name")
    board = serializers.CharField(source="board.name")

    class Meta:
        model = Paper
        fields = [
            'id',
            'title',
            'exam_name',
            'school_class',
            'subject',
            'board',
            'max_marks',
            'duration',
            'created_at'
        ]


class PaperQuestionSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.question_text")
    type = serializers.CharField(source="question.get_type_display")
    difficulty = serializers.CharField(source="question.difficulty")
    answer = serializers.JSONField(source="question.answer")
    options = serializers.JSONField(source="question.options")

    class Meta:
        model = PaperQuestion
        fields = ["id", "question_text", "options", "answer", "marks", "order", "type", "difficulty"]

class PaperSectionSerializer(serializers.ModelSerializer):
    questions = PaperQuestionSerializer(
        source="paper_questions",
        many=True
    )

    class Meta:
        model = PaperSection
        fields = ["id", "name", "order", "questions"]

class PaperDetailSerializer(serializers.ModelSerializer):
    sections = PaperSectionSerializer(many=True)
    school_class = serializers.CharField(source="school_class.name")
    subject = serializers.CharField(source="subject.name")
    board = serializers.CharField(source="board.name")

    class Meta:
        model = Paper
        fields = [
            "id",
            "title",
            "exam_name",
            "school_class",
            "subject",
            "board",
            "max_marks",
            "duration",
            "created_at",
            "sections"
        ]