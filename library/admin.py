from django.contrib import admin

from .models import Book, BookCopy, BookIssue, BookRequest, BookRenewal, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'role', 'branch', 'roll_number')
	list_filter = ('role',)
	search_fields = ('user__username', 'user__email', 'branch', 'roll_number')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
	list_display = ('title', 'author', 'isbn', 'barcode_number', 'category', 'total_copies', 'issued_count', 'available_copies')
	search_fields = ('title', 'author', 'isbn', 'barcode_number', 'category')
	list_filter = ('category',)


@admin.register(BookCopy)
class BookCopyAdmin(admin.ModelAdmin):
	list_display = ('copy_code', 'book', 'copy_number', 'status', 'created_at')
	search_fields = ('copy_code', 'book__title', 'book__isbn')
	list_filter = ('status', 'book__category')


@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
	list_display = ('member', 'book', 'copy', 'issued_at', 'due_date', 'returned_at', 'fine_amount')
	search_fields = ('member__username', 'book__title', 'book__author', 'copy__copy_code')
	list_filter = ('due_date', 'returned_at')


@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
	list_display = ('member', 'book', 'status', 'requested_at', 'reviewed_at', 'reviewed_by')
	search_fields = ('member__username', 'book__title', 'book__isbn', 'note')
	list_filter = ('status', 'requested_at')


@admin.register(BookRenewal)
class BookRenewalAdmin(admin.ModelAdmin):
	list_display = ('member', 'issue', 'status', 'requested_at', 'reviewed_at', 'reviewed_by', 'new_due_date')
	search_fields = ('member__username', 'issue__book__title', 'issue__book__isbn', 'reason')
	list_filter = ('status', 'requested_at')
