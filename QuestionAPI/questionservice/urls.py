from django.urls import path
from .views import (
    BoardList, ClassList, MyPapersView, SubjectList, BookList,
    ChapterList, QuestionList, QuestionDetail, chatbot_generate_question,
    get_subjects_by_class, get_questions, get_books, get_chapters_by_book, get_class_name, get_subject_name, get_board_name, get_questions_by_chapters,
    CreateFullPaperView,
    SignupView, LoginView,
    MyPapersView
)

urlpatterns = [
    path('boards/', BoardList.as_view(), name='board-list'),
    path('classes/', ClassList.as_view(), name='class-list'),
    path('subjects/', SubjectList.as_view(), name='subject-list'),
    path('books/', BookList.as_view(), name='book-list'),
    path('chapters/', ChapterList.as_view(), name='chapter-list'),
    path('questions/', QuestionList.as_view(), name='question-list'),
    path('questions/<int:pk>/', QuestionDetail.as_view(), name='question-detail'),
    # path('subjects/', get_subjects_by_class, name='subjects-by-class'),
    # path('subjects/by-class/', get_subjects_by_class, name='subjects-by-class'),
    path('subjects/by-class/<int:class_id>/', get_subjects_by_class, name='subjects-by-class'),
    path('questions/', get_questions, name='questions'),
    path('books/by-filters/', get_books, name='books-by-filters'),
    path('chapters/by-book/', get_chapters_by_book, name='chapters-by-book'),
    path('classes/name/', get_class_name, name='class-name'),
    path('subjects/name/', get_subject_name, name='subject-name'),
    path('boards/name/', get_board_name, name='board-name'),
    path('questions/by-chapters/', get_questions_by_chapters),
    # path('signup/', signup),
    # path('login/', login),
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    # path('my-papers/', MyPaperView.as_view(), name='my-papers'),
    path("papers/create/", CreateFullPaperView.as_view(), name="create-paper"),
    path('my-papers/', MyPapersView.as_view(), name='my-papers'),
    path("chatbot/generate/", chatbot_generate_question, name="chatbot_generate"),
]
