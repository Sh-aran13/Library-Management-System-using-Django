from datetime import timedelta
from decimal import Decimal

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Book, BookIssue, BookRequest, BookRenewal, Profile


class StudentRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    branch = forms.CharField(max_length=120, required=True)
    roll_number = forms.CharField(max_length=50, required=True)

    def clean_roll_number(self):
        roll_number = self.cleaned_data['roll_number'].strip()
        if Profile.objects.filter(roll_number__iexact=roll_number).exists():
            raise forms.ValidationError('This roll number is already registered.')
        return roll_number

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'branch', 'roll_number', 'password1', 'password2')


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ('title', 'author', 'isbn', 'category', 'description', 'total_copies')


class BookRequestForm(forms.ModelForm):
    class Meta:
        model = BookRequest
        fields = ('note',)


class BookRenewalForm(forms.ModelForm):
    class Meta:
        model = BookRenewal
        fields = ('reason',)


class IssueBookForm(forms.ModelForm):
    ISSUE_PERIOD_DAYS = 14

    member = forms.ModelChoiceField(queryset=User.objects.none())

    class Meta:
        model = BookIssue
        fields = ('member', 'book')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['book'].queryset = Book.objects.all().order_by('title')
        self.fields['member'].queryset = User.objects.filter(groups__name='Student').order_by('username').distinct()

    def clean_book(self):
        book = self.cleaned_data['book']
        if book.available_copies <= 0:
            raise forms.ValidationError('This book is currently unavailable.')
        return book

    def save(self, commit=True):
        issue = super().save(commit=False)
        issue.due_date = timezone.now().date() + timedelta(days=self.ISSUE_PERIOD_DAYS)
        issue.fine_per_day = Decimal('2.00')
        if commit:
            issue.save()
        return issue


class QuickCheckoutForm(forms.Form):
    ISSUE_PERIOD_DAYS = 14

    member_username = forms.CharField(max_length=150, help_text='Student username for check-in (issue)')
    book_isbn = forms.CharField(max_length=20, help_text='Book ISBN to check in (issue)')

    def clean_member_username(self):
        username = self.cleaned_data['member_username'].strip()
        try:
            member = User.objects.get(username__iexact=username, groups__name='Student')
        except User.DoesNotExist as exc:
            raise ValidationError('Student username not found.') from exc
        self.cleaned_data['member'] = member
        return username

    def clean_book_isbn(self):
        isbn = self.cleaned_data['book_isbn'].strip()
        try:
            book = Book.objects.get(isbn=isbn)
        except Book.DoesNotExist as exc:
            raise ValidationError('Book ISBN not found.') from exc
        self.cleaned_data['book'] = book
        return isbn


class QuickCheckinForm(forms.Form):
    member_username = forms.CharField(max_length=150, help_text='Student username for check-out (return)')
    book_isbn = forms.CharField(max_length=20, help_text='Book ISBN to check out (return)')

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('member_username', '').strip()
        isbn = cleaned_data.get('book_isbn', '').strip()

        if not username or not isbn:
            return cleaned_data

        try:
            issue = (
                BookIssue.objects.select_related('member', 'book')
                .filter(
                    member__username__iexact=username,
                    member__groups__name='Student',
                    book__isbn=isbn,
                    returned_at__isnull=True,
                )
                .latest('issued_at')
            )
        except BookIssue.DoesNotExist as exc:
            raise ValidationError('No active issued record found for this student and ISBN.') from exc

        cleaned_data['issue'] = issue
        return cleaned_data
