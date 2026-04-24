from datetime import timedelta
from decimal import Decimal
import random

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class Profile(models.Model):
	ROLE_CHOICES = (
		('librarian', 'Librarian'),
		('student', 'Student'),
	)

	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
	role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
	branch = models.CharField(max_length=120, blank=True)
	roll_number = models.CharField(max_length=50, unique=True, null=True, blank=True)

	def __str__(self):
		return f"{self.user.username} ({self.get_role_display()})"


class Book(models.Model):
	title = models.CharField(max_length=255)
	author = models.CharField(max_length=255)
	isbn = models.CharField(max_length=20, unique=True)
	barcode_number = models.CharField(max_length=16, unique=True, blank=True, null=True, db_index=True)
	category = models.CharField(max_length=100)
	description = models.TextField(blank=True)
	total_copies = models.PositiveIntegerField(default=1)

	class Meta:
		ordering = ('title',)

	def __str__(self):
		return f"{self.title} by {self.author}"

	@property
	def issued_count(self):
		copy_count = self.copies.filter(status=BookCopy.STATUS_ISSUED).count()
		if copy_count:
			return copy_count
		return self.issues.filter(returned_at__isnull=True).count()

	@property
	def available_copies(self):
		if self.copies.exists():
			return self.copies.filter(status=BookCopy.STATUS_AVAILABLE).count()
		return max(self.total_copies - self.issued_count, 0)

	@property
	def is_available(self):
		return self.available_copies > 0

	def ensure_copy_inventory(self):
		"""Create missing physical copies up to total_copies."""
		existing_count = self.copies.count()
		if existing_count >= self.total_copies:
			return
		for copy_number in range(existing_count + 1, self.total_copies + 1):
			BookCopy.objects.create(book=self, copy_number=copy_number)

	def get_available_copy(self):
		copy_qs = self.copies.filter(status=BookCopy.STATUS_AVAILABLE).order_by('copy_number')
		if transaction.get_connection().in_atomic_block:
			copy_qs = copy_qs.select_for_update()
		return copy_qs.first()

	def issue_to_member(self, member, due_days=14):
		copy = self.get_available_copy()
		if not copy:
			raise ValueError('This book is currently unavailable.')
		issue = BookIssue(
			member=member,
			book=self,
			copy=copy,
			due_date=BookIssue.default_due_date(due_days),
			fine_per_day=BookIssue.FINE_PER_DAY_INR,
		)
		issue.save()
		copy.status = BookCopy.STATUS_ISSUED
		copy.save(update_fields=['status'])
		return issue

	def allocate_waitlisted_requests(self, reviewed_by=None):
		"""Auto-issue available copies to the oldest pending requests."""
		allocated_issues = []
		while True:
			copy = self.get_available_copy()
			request_qs = self.requests.filter(status=BookRequest.STATUS_PENDING).order_by('requested_at', 'pk')
			if transaction.get_connection().in_atomic_block:
				request_qs = request_qs.select_for_update()
			request = request_qs.first()
			if not copy or not request:
				break
			issue = BookIssue(
				member=request.member,
				book=self,
				copy=copy,
				due_date=BookIssue.default_due_date(14),
				fine_per_day=BookIssue.FINE_PER_DAY_INR,
			)
			issue.save()
			copy.status = BookCopy.STATUS_ISSUED
			copy.save(update_fields=['status'])
			request.status = BookRequest.STATUS_ISSUED
			request.reviewed_by = reviewed_by
			request.reviewed_at = timezone.now()
			request.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
			allocated_issues.append(issue)
		return allocated_issues

	@staticmethod
	def generate_barcode_number():
		# Prefix keeps numbers recognizable as book inventory codes.
		return f"BK{random.randint(1000000000, 9999999999)}"

	def save(self, *args, **kwargs):
		if not self.barcode_number:
			candidate = self.generate_barcode_number()
			while Book.objects.filter(barcode_number=candidate).exists():
				candidate = self.generate_barcode_number()
			self.barcode_number = candidate
		super().save(*args, **kwargs)
		self.ensure_copy_inventory()


class BookCopy(models.Model):
	STATUS_AVAILABLE = 'available'
	STATUS_ISSUED = 'issued'
	STATUS_LOST = 'lost'
	STATUS_MAINTENANCE = 'maintenance'

	STATUS_CHOICES = (
		(STATUS_AVAILABLE, 'Available'),
		(STATUS_ISSUED, 'Issued'),
		(STATUS_LOST, 'Lost'),
		(STATUS_MAINTENANCE, 'Maintenance'),
	)

	book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='copies')
	copy_number = models.PositiveIntegerField()
	copy_code = models.CharField(max_length=32, unique=True, blank=True, null=True, db_index=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE)
	note = models.CharField(max_length=255, blank=True)
	created_at = models.DateTimeField(default=timezone.now)

	class Meta:
		ordering = ('book__title', 'copy_number')
		unique_together = (('book', 'copy_number'),)

	def __str__(self):
		return f"{self.book.title} - Copy {self.copy_number} ({self.get_status_display()})"

	@staticmethod
	def generate_copy_code(book, copy_number):
		book_key = book.barcode_number or f"BK{book.pk or 'NEW'}"
		return f"{book_key}-C{copy_number:03d}"

	def save(self, *args, **kwargs):
		if not self.copy_code:
			self.copy_code = self.generate_copy_code(self.book, self.copy_number)
		super().save(*args, **kwargs)


class BookIssue(models.Model):
	FINE_PER_DAY_INR = Decimal('2.00')

	member = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='borrowed_books',
	)
	book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='issues')
	copy = models.ForeignKey(BookCopy, on_delete=models.SET_NULL, null=True, blank=True, related_name='issues')
	issued_at = models.DateTimeField(default=timezone.now)
	due_date = models.DateField()
	returned_at = models.DateTimeField(null=True, blank=True)
	fine_amount = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal('0.00'))
	fine_per_day = models.DecimalField(max_digits=6, decimal_places=2, default=FINE_PER_DAY_INR)

	class Meta:
		ordering = ('-issued_at',)

	def __str__(self):
		return f"{self.member.username} -> {self.book.title}"

	@staticmethod
	def default_due_date(days=14):
		return timezone.now().date() + timedelta(days=days)

	@property
	def is_overdue(self):
		if self.returned_at:
			return self.returned_at.date() > self.due_date
		return timezone.now().date() > self.due_date

	@property
	def overdue_days(self):
		end_date = self.returned_at.date() if self.returned_at else timezone.now().date()
		days = (end_date - self.due_date).days
		return max(days, 0)

	def calculate_fine(self):
		# LMS tiered fine policy:
		# Days 1-7: ₹2/day | Days 8-30: ₹5/day (cumulative) | Days 31+: ₹10/day (cumulative)
		days = self.overdue_days
		if days <= 7:
			return Decimal(days) * Decimal('2.00')
		elif days <= 30:
			return Decimal('14.00') + (Decimal(days - 7) * Decimal('5.00'))
		else:
			return Decimal('129.00') + (Decimal(days - 30) * Decimal('10.00'))

	def mark_returned(self):
		if not self.returned_at:
			self.returned_at = timezone.now()
			self.fine_amount = self.calculate_fine()
			self.save(update_fields=['returned_at', 'fine_amount'])
			if self.copy and self.copy.status == BookCopy.STATUS_ISSUED:
				self.copy.status = BookCopy.STATUS_AVAILABLE
				self.copy.save(update_fields=['status'])


class BookRequest(models.Model):
	STATUS_PENDING = 'pending'
	STATUS_ISSUED = 'issued'
	STATUS_REJECTED = 'rejected'

	STATUS_CHOICES = (
		(STATUS_PENDING, 'Pending'),
		(STATUS_ISSUED, 'Issued'),
		(STATUS_REJECTED, 'Rejected'),
	)

	member = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='book_requests',
	)
	book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='requests')
	note = models.CharField(max_length=255, blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	requested_at = models.DateTimeField(default=timezone.now)
	reviewed_at = models.DateTimeField(null=True, blank=True)
	reviewed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='reviewed_book_requests',
	)

	class Meta:
		ordering = ('-requested_at',)

	def __str__(self):
		return f"{self.member.username} requested {self.book.title} ({self.status})"


class BookRenewal(models.Model):
	STATUS_PENDING = 'pending'
	STATUS_APPROVED = 'approved'
	STATUS_REJECTED = 'rejected'

	STATUS_CHOICES = (
		(STATUS_PENDING, 'Pending'),
		(STATUS_APPROVED, 'Approved'),
		(STATUS_REJECTED, 'Rejected'),
	)

	issue = models.ForeignKey(
		BookIssue,
		on_delete=models.CASCADE,
		related_name='renewals',
	)
	member = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='book_renewals',
	)
	reason = models.CharField(max_length=255, blank=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
	requested_at = models.DateTimeField(default=timezone.now)
	reviewed_at = models.DateTimeField(null=True, blank=True)
	reviewed_by = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.SET_NULL,
		null=True,
		blank=True,
		related_name='reviewed_book_renewals',
	)
	new_due_date = models.DateField(null=True, blank=True)

	class Meta:
		ordering = ('-requested_at',)

	def __str__(self):
		return f"{self.member.username} renewal request for {self.issue.book.title} ({self.status})"
