import django_filters
from .models import Question

class QuestionFilter(django_filters.FilterSet):
    chapter_id = django_filters.NumberFilter(field_name='chapter__id')
    book_id = django_filters.NumberFilter(field_name='book__id')
    subject_id = django_filters.NumberFilter(field_name='subject__id')
    type = django_filters.CharFilter(field_name='type')
    difficulty = django_filters.CharFilter(field_name='difficulty')

    class Meta:
        model = Question
        fields = ['chapter_id','book_id','subject_id','type','difficulty']
