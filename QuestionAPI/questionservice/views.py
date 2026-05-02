from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from .models import Board, SchoolClass, Subject, Book, Chapter, Question, User, Paper, PaperSection, PaperQuestion
from .serializers import (
    BoardSerializer, SchoolClassSerializer, SubjectSerializer,
    BookSerializer, ChapterSerializer, QuestionSerializer,
    SignupSerializer, LoginSerializer, PaperListSerializer,
    PaperDetailSerializer
)
from .filters import QuestionFilter
from rest_framework_simplejwt.tokens import RefreshToken

from .gemini_client import GeminiClient
from .prompts import SYSTEM_PROMPT
import json



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


class MyPapersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        papers = Paper.objects.filter(user=self.request.user).order_by("-created_at")
        serializer = PaperDetailSerializer(papers, many=True)
        return Response(serializer.data)

# views.py

from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.shortcuts import get_object_or_404

class CreateFullPaperView(APIView):
    # permission_classes = [IsAuthenticated]
    print("CreateFullPaperView loaded")  # Debug print
    @transaction.atomic
    def post(self, request):

        try:
            print("User:", request.user)
            data = request.data
            print("Received data for paper creation:", data)  # Debug print
            paper_details = data.get("paperDetails")
            sections = data.get("sections", [])
            instruction_list = paper_details.get("instructions", "")
            exam_instructions = "\n".join(instruction_list) if instruction_list else ""

            # 🔹 Create Paper
            paper = Paper.objects.create(
                user=request.user,
                title=paper_details["examName"],
                school_name=paper_details["schoolName"],
                exam_name=paper_details["examName"],
                school_class_id=paper_details["class_id"],
                subject_id=paper_details["subject_id"],
                board_id=paper_details["board_id"],
                max_marks=paper_details["maxMarks"],
                duration=paper_details["time"],
                exam_instructions=exam_instructions
            )

            print("Paper created with ID:", paper.id,)  # Debug print

            # 🔹 Create Sections + Link Questions
            for section_index, section in enumerate(sections):
                paper_section = PaperSection.objects.create(
                    paper=paper,
                    name=section["sectionTitle"],
                    order=section_index
                )
                print(f"  Section '{paper_section.name}' created with ID: {paper_section.id}")  # Debug print

                for question_index, q in enumerate(section["questions"]):
                    question_id = q.get("question_id")

                    if isinstance(question_id, str) and question_id.startswith(('custom-', 'ai-q-', 'match-', 'merged-')):
                        # Determine question type based on prefix
                        if question_id.startswith('match-'):
                            q_type = 'match'
                        elif question_id.startswith('merged-'):
                            q_type = q.get("type", "short")  # default to short if not provided
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
                        print(f"    Book '{book.title}' (ID: {book.id}) - {'Created' if created else 'Exists'}")  # Debug print
                        # Get or create custom chapter
                        chapter, created = Chapter.objects.get_or_create(
                            book=book,
                            chapter_number=1,
                            defaults={'name': 'Custom Chapter'}
                        )
                        print(f"    Chapter '{chapter.name}' (ID: {chapter.id}) - {'Created' if created else 'Exists'}")  # Debug print
                        # Create question
                        question = Question.objects.create(
                            book=book,
                            chapter=chapter,
                            subject=paper.subject,
                            question_text=q.get("question", ""),
                            answer=q.get("answer", {}),
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
                    print(f"    Question '{question.question_text}' created with ID: {question.id}")  # Debug print
        except Exception as e:
            print("Error during paper creation:", str(e))
            return Response(
                {"success": False, "message": "Failed to create paper", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response({
            "success": True,
            "message": "Paper created successfully"
        })


from rest_framework import status
import json
import uuid

@api_view(['POST'])
def chatbot_generate_question(request):
    print("Chatbot Request:", request.data)

    user_query = request.data.get("message", "")
    print("User_Query:", user_query)

    if not user_query:
        return Response(
            {"error": "Query parameter is required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    messages = [
        {"role": "user", "parts": [{"text": user_query}]}
    ]

    try:
        gemini_client = GeminiClient()
        response = gemini_client.generate_text(
            messages=messages,
            system_instruction=SYSTEM_PROMPT,
            model="gemini-2.5-flash"
        )
    except Exception as e:
        print("Error calling Gemini API:", str(e))
        return Response(
            {"error": "Failed to generate questions"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    try:
        if response.startswith("```json") and response.endswith("```"):
            response = response[len("```json"): -len("```")].strip()

        response_json = json.loads(response)
        print("Gemini response:", response_json)

        if response_json.get("flag"):
            # generate unique IDs for AI-generated questions using uuid
            for q in response_json.get("questions", []):
                q["id"] = f"ai-q-{uuid.uuid4()}"
            
            print("resposne after adding IDs:", response_json)
            return Response({
                "success": True,
                "questions": response_json.get("questions", [])
            })

        return Response({
            "success": False,
            "message": f"Missing fields: {', '.join(response_json.get('missing', []))}"
        }, status=status.HTTP_400_BAD_REQUEST)

    except json.JSONDecodeError:
        return Response(
            {"error": "Failed to parse model response"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
