from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Board, SchoolClass, Subject, Book, Chapter, Question, User, Paper, PaperSection, PaperQuestion
from .serializers import (
    BoardSerializer, SchoolClassSerializer, SubjectSerializer,
    BookSerializer, ChapterSerializer, QuestionSerializer,
    SignupSerializer, LoginSerializer, PaperListSerializer
)
from .filters import QuestionFilter
from rest_framework_simplejwt.tokens import RefreshToken

# @api_view(['POST'])
# def signup(request):
#     serializer = SignupSerializer(data=request.data)
#     if serializer.is_valid():
#         serializer.save()
#         return Response({
#             "success": True,
#             "message": "Account created successfully! Please login.",
#             "user": serializer.data
#         })
#     return Response({
#         "success": False,
#         "message": serializer.errors
#     })

from rest_framework.views import APIView

class SignupView(APIView):
    def post(self, request):
        print("Signup User Data: ",request.data)
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "User created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# def login(request):
    # serializer = LoginSerializer(data=request.data)
    # if serializer.is_valid():
    #     user = serializer.validated_data

    #     refresh = RefreshToken.for_user(user)

    #     return Response({
    #         "success": True,
    #         "message": "Login successful!",
    #         "access_token": str(refresh.access_token),
    #         "refresh_token": str(refresh),
    #         "user": {
    #             "id": user.id,
    #             "name": user.name,
    #             "email": user.email,
    #             "created_at": user.created_at,
    #             "updated_at": user.updated_at
    #         }
    #     })
    # return Response({
    #     "success": False,
    #     "message": "Invalid email or password."
    # })
class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(
            data=request.data,
            context={"request": request}
        )

        if serializer.is_valid():
            user = serializer.validated_data
            print(dir(user))
            refresh = RefreshToken.for_user(user)
            exp = refresh.access_token['exp']
            exp_time = exp - int(refresh.current_time.timestamp())
            # print("Expiration Time:", refresh.access_token['exp'])
            print("Expiration Time (in seconds):", exp_time)
            print("User:",user,"Name:",user.email)
            return Response({
                "success": True,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                },
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
# Simple list endpoints
class BoardList(generics.ListAPIView):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [permissions.AllowAny]

class ClassList(generics.ListAPIView):
    queryset = SchoolClass.objects.all()
    serializer_class = SchoolClassSerializer
    permission_classes = [permissions.AllowAny]

class SubjectList(generics.ListAPIView):
    serializer_class = SubjectSerializer
    permission_classes = [permissions.AllowAny]
    def get_queryset(self):
        qs = Subject.objects.all()
        board = self.request.query_params.get('board_id')
        cls = self.request.query_params.get('class_id')
        if board:
            qs = qs.filter(board_id=board)
        if cls:
            qs = qs.filter(school_class_id=cls)
        return qs

class BookList(generics.ListAPIView):
    serializer_class = BookSerializer
    permission_classes = [permissions.AllowAny]
    def get_queryset(self):
        qs = Book.objects.select_related('subject','board','school_class').all()
        board = self.request.query_params.get('board_id')
        cls = self.request.query_params.get('class_id')
        subj = self.request.query_params.get('subject_id')
        if board: qs = qs.filter(board_id=board)
        if cls: qs = qs.filter(school_class_id=cls)
        if subj: qs = qs.filter(subject_id=subj)
        return qs

class ChapterList(generics.ListAPIView):
    serializer_class = ChapterSerializer
    permission_classes = [permissions.AllowAny]
    def get_queryset(self):
        book_id = self.request.query_params.get('book_id')
        qs = Chapter.objects.all()
        if book_id: qs = qs.filter(book_id=book_id)
        return qs

# Questions list: filterable + searchable + paginated
class QuestionList(generics.ListCreateAPIView):
    queryset = Question.objects.select_related('book','chapter','subject').all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.AllowAny]  # For create, change to IsAdminUser
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = QuestionFilter
    search_fields = ['question_text', 'options']  # Search in question text and options (JSON string)
    ordering_fields = ['marks', 'difficulty', 'created_at']

    def perform_create(self, serializer):
        # restrict create to admins in real app
        serializer.save(created_by=self.request.user)

class QuestionDetail(generics.RetrieveAPIView):
    queryset = Question.objects.select_related('book','chapter','subject').all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.AllowAny]

# GET /api/v1/subjects/?class_id=1
@api_view(['GET'])
def get_subjects_by_class(request, class_id):
    if not class_id:
        return Response({"error": "class_id is required"}, status=400)
    print("Received class_id:", class_id)  # Debug print
    subjects = Subject.objects.filter(school_class_id=class_id)
    serializer = SubjectSerializer(subjects, many=True)
    return Response(serializer.data)

# GET /api/v1/questions/?chapter_id=1&book_id=&subject_id=&type=Short+Answer&difficulty=Easy
@api_view(['GET'])
def get_questions(request):
    chapter_id = request.GET.get("chapter_id")
    q_type = request.GET.get("type")
    difficulty = request.GET.get("difficulty")

    # Base queryset
    questions = Question.objects.all()

    # Apply filters if provided
    if chapter_id:
        questions = questions.filter(chapter_id=chapter_id)
    if q_type:
        questions = questions.filter(type=q_type)
    if difficulty:
        questions = questions.filter(difficulty=difficulty)

    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def get_books(request):
    class_id = request.GET.get("class_id")
    subject_id = request.GET.get("subject_id")
    board_id = request.GET.get("board_id")

    if not class_id or not subject_id or not board_id:
        return Response(
            {"error": "class_id, subject_id and board_id are required"},
            status=400
        )

    books = Book.objects.filter(
        school_class_id=class_id,
        subject_id=subject_id,
        board_id=board_id
    ).order_by('title')

    serializer = BookSerializer(books, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_chapters_by_book(request):
    book_id = request.GET.get("book_id")

    if not book_id:
        return Response({"error": "book_id is required"}, status=400)

    chapters = Chapter.objects.filter(
        book_id=book_id
    ).order_by('chapter_number')

    serializer = ChapterSerializer(chapters, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_class_name(request):
    class_id = request.GET.get("class_id")

    if not class_id:
        return Response({"error": "class_id is required"}, status=400)

    try:
        school_class = SchoolClass.objects.get(id=class_id)
        return Response({"name": school_class.name})
    except SchoolClass.DoesNotExist:
        return Response({"name": "Unknown Class"})

@api_view(['GET'])
def get_subject_name(request):
    subject_id = request.GET.get("subject_id")

    if not subject_id:
        return Response({"error": "subject_id is required"}, status=400)

    try:
        subject = Subject.objects.get(id=subject_id)
        return Response({"name": subject.name})
    except Subject.DoesNotExist:
        return Response({"name": "Unknown Subject"})

@api_view(['GET'])
def get_board_name(request):
    board_id = request.GET.get("board_id")

    if not board_id:
        return Response({"error": "board_id is required"}, status=400)

    try:
        board = Board.objects.get(id=board_id)
        return Response({"name": board.name})
    except Board.DoesNotExist:
        return Response({"name": "Unknown Board"})

@api_view(['GET'])
def get_questions_by_chapters(request):
    chapter_ids = request.GET.getlist('chapter_ids')

    if not chapter_ids:
        return Response([], status=200)

    questions = Question.objects.filter(
        chapter_id__in=chapter_ids
    )

    serializer = QuestionSerializer(questions, many=True)
    return Response(serializer.data)

class MyPaperView(generics.ListAPIView):
    serializer_class = PaperListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Paper.objects.filter(user=self.request.user).order_by('-created_at')


# views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404

class CreateFullPaperView(APIView):
    # permission_classes = [IsAuthenticated]
    print("CreateFullPaperView loaded")  # Debug print
    @transaction.atomic
    def post(self, request):
        print("User:", request.user)

        data = request.data
        print("Received data for paper creation:", data)  # Debug print
        paper_details = data.get("paperDetails")
        sections = data.get("sections", [])

        # 🔹 Create Paper
        paper = Paper.objects.create(
            user=request.user,
            title=paper_details["examName"],
            exam_name=paper_details["examName"],
            school_class_id=paper_details["class_id"],
            subject_id=paper_details["subject_id"],
            board_id=paper_details["board_id"],
            max_marks=paper_details["maxMarks"],
            duration=paper_details["time"],
        )

        # 🔹 Create Sections + Link Questions
        for section_index, section in enumerate(sections):
            paper_section = PaperSection.objects.create(
                paper=paper,
                name=section["sectionTitle"],
                order=section_index
            )

            for question_index, q in enumerate(section["questions"]):
                question_id = q.get("question_id")

                if isinstance(question_id, str) and question_id.startswith(('custom-', 'ai-q-', 'match-')):
                    # Determine question type based on prefix
                    if question_id.startswith('match-'):
                        q_type = 'match'
                    else:
                        q_type = 'short'  # for custom- and ai-q-

                    # Get or create custom book
                    book, created = Book.objects.get_or_create(
                        title="Custom Questions",
                        board_id=paper.board_id,
                        school_class_id=paper.school_class_id,
                        subject_id=paper.subject_id,
                        defaults={'author': 'AI/Custom'}
                    )
                    # Get or create custom chapter
                    chapter, created = Chapter.objects.get_or_create(
                        book=book,
                        chapter_number=1,
                        defaults={'name': 'Custom Chapter'}
                    )
                    # Create question
                    question = Question.objects.create(
                        book=book,
                        chapter=chapter,
                        subject=paper.subject,
                        question_text=q.get("question", ""),
                        type=q_type,
                        difficulty='medium',
                        marks=q.get("marks", 1),
                        created_by=request.user
                    )
                else:
                    question = get_object_or_404(Question, id=question_id)

                PaperQuestion.objects.create(
                    paper_section=paper_section,
                    question=question,
                    marks=q.get("marks", 1),
                    order=question_index
                )

        return Response({
            "success": True,
            "message": "Paper created successfully"
        })
