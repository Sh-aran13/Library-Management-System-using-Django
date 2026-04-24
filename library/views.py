from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .forms import BookForm, BookRequestForm, BookRenewalForm, IssueBookForm, QuickCheckinForm, QuickCheckoutForm, StudentRegistrationForm
from .models import Book, BookIssue, BookRequest, BookRenewal


def is_librarian(user):
	return user.is_superuser or user.groups.filter(name='Librarian').exists()


def is_student(user):
	return user.groups.filter(name='Student').exists()


def _librarian_stats():
	total_books = Book.objects.count()
	active_issues = BookIssue.objects.filter(returned_at__isnull=True).count()
	overdue_issues = BookIssue.objects.filter(returned_at__isnull=True, due_date__lt=BookIssue.default_due_date(0)).count()
	total_students = Group.objects.filter(name='Student').first()
	student_count = total_students.user_set.count() if total_students else 0
	return {
		'total_books': total_books,
		'active_issues': active_issues,
		'overdue_issues': overdue_issues,
		'student_count': student_count,
	}


def home(request):
	if request.user.is_authenticated:
		return redirect('dashboard')
	return redirect('login')


def student_signup(request):
	if request.method == 'POST':
		form = StudentRegistrationForm(request.POST)
		if form.is_valid():
			user = form.save()
			student_group, _ = Group.objects.get_or_create(name='Student')
			user.groups.add(student_group)
			user.profile.role = 'student'
			user.profile.branch = form.cleaned_data['branch'].strip()
			user.profile.roll_number = form.cleaned_data['roll_number'].strip()
			user.profile.save(update_fields=['role', 'branch', 'roll_number'])
			messages.success(request, 'Registration successful. Please login to continue.')
			return redirect('login')
	else:
		form = StudentRegistrationForm()
	return render(request, 'library/student_signup.html', {'form': form})


@login_required
def dashboard(request):
	if is_librarian(request.user):
		stats = _librarian_stats()
		recent_issues = BookIssue.objects.select_related('book', 'member')[:8]
		return render(
			request,
			'library/librarian_dashboard.html',
			{
				**stats,
				'recent_issues': recent_issues,
			},
		)

	current_borrowings = list(BookIssue.objects.filter(member=request.user, returned_at__isnull=True).select_related('book'))
	today = timezone.now().date()
	total_fine = Decimal('0.00')
	for issue in current_borrowings:
		total_days = max((issue.due_date - issue.issued_at.date()).days, 1)
		remaining_days = (issue.due_date - today).days
		clamped_remaining = max(min(remaining_days, total_days), 0)
		issue.due_progress_pct = int((clamped_remaining / total_days) * 100)
		issue.due_remaining_days = remaining_days
		issue.live_fine_amount = issue.calculate_fine() if issue.is_overdue else Decimal('0.00')
		total_fine += issue.live_fine_amount
		if remaining_days <= 2:
			issue.due_progress_state = 'danger'
		elif remaining_days <= 5:
			issue.due_progress_state = 'warning'
		else:
			issue.due_progress_state = 'safe'
	borrowing_history = BookIssue.objects.filter(member=request.user).select_related('book')[:10]
	book_requests = BookRequest.objects.filter(member=request.user).select_related('book')[:10]
	book_renewals = BookRenewal.objects.filter(member=request.user).select_related('issue__book')[:10]
	return render(
		request,
		'library/student_dashboard.html',
		{
			'current_borrowings': current_borrowings,
			'total_fine': total_fine,
			'borrowing_history': borrowing_history,
			'book_requests': book_requests,
			'book_renewals': book_renewals,
		},
	)


@login_required
def book_list(request):
	query = request.GET.get('q', '').strip()
	category = request.GET.get('category', '').strip()

	books = Book.objects.all()
	if query:
		books = books.filter(
			Q(title__icontains=query) | Q(author__icontains=query) | Q(category__icontains=query) | Q(isbn__icontains=query)
		)
	if category:
		books = books.filter(category__icontains=category)

	pending_request_book_ids = set()
	if is_student(request.user):
		pending_request_book_ids = set(
			BookRequest.objects.filter(member=request.user, status=BookRequest.STATUS_PENDING).values_list('book_id', flat=True)
		)

	categories = Book.objects.values_list('category', flat=True).distinct().order_by('category')
	return render(
		request,
		'library/book_list.html',
		{
			'books': books,
			'query': query,
			'selected_category': category,
			'categories': categories,
			'is_librarian': is_librarian(request.user),
			'is_student': is_student(request.user),
			'pending_request_book_ids': pending_request_book_ids,
		},
	)


@login_required
@user_passes_test(is_librarian)
def book_barcode_detail(request, barcode_number):
	book = get_object_or_404(Book, barcode_number=barcode_number)
	return render(
		request,
		'library/book_barcode_detail.html',
		{
			'book': book,
		},
	)


@login_required
@user_passes_test(is_librarian)
def book_create(request):
	if request.method == 'POST':
		form = BookForm(request.POST)
		if form.is_valid():
			form.save()
			messages.success(request, 'Book added successfully.')
			return redirect('book_list')
	else:
		form = BookForm()
	return render(request, 'library/book_form.html', {'form': form, 'page_title': 'Add Book'})


@login_required
@user_passes_test(is_librarian)
def book_update(request, pk):
	book = get_object_or_404(Book, pk=pk)
	if request.method == 'POST':
		form = BookForm(request.POST, instance=book)
		if form.is_valid():
			form.save()
			messages.success(request, 'Book updated successfully.')
			return redirect('book_list')
	else:
		form = BookForm(instance=book)
	return render(request, 'library/book_form.html', {'form': form, 'page_title': 'Edit Book'})


@login_required
@user_passes_test(is_librarian)
def book_delete(request, pk):
	book = get_object_or_404(Book, pk=pk)
	if request.method == 'POST':
		book.delete()
		messages.success(request, 'Book deleted successfully.')
		return redirect('book_list')
	return render(request, 'library/book_confirm_delete.html', {'book': book})


@login_required
@user_passes_test(is_librarian)
def issue_book(request):
	book_request = None
	request_id = request.GET.get('request') if request.method == 'GET' else request.POST.get('request_id')

	if request_id:
		book_request = get_object_or_404(BookRequest, pk=request_id)
		if book_request.status != BookRequest.STATUS_PENDING:
			messages.info(request, 'This request is already processed.')
			return redirect('book_requests')

	if request.method == 'POST':
		post_data = request.POST
		if book_request:
			# Enforce the request's member/book even if POST payload is tampered.
			post_data = request.POST.copy()
			post_data['member'] = str(book_request.member_id)
			post_data['book'] = str(book_request.book_id)
		form = IssueBookForm(post_data)
		if form.is_valid():
			with transaction.atomic():
				locked_book = Book.objects.select_for_update().get(pk=form.cleaned_data['book'].pk)
				member = form.cleaned_data['member']
				try:
					locked_book.issue_to_member(member, due_days=IssueBookForm.ISSUE_PERIOD_DAYS)
				except ValueError:
					form.add_error('book', 'This book became unavailable just now. Please retry.')
				else:
					if book_request:
						book_request.status = BookRequest.STATUS_ISSUED
						book_request.reviewed_by = request.user
						book_request.reviewed_at = timezone.now()
						book_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
					messages.success(request, 'Book issued successfully.')
					return redirect('manage_issues')
	else:
		initial = {}
		if book_request:
			initial = {'member': book_request.member, 'book': book_request.book}
		form = IssueBookForm(initial=initial)
	return render(request, 'library/issue_book.html', {'form': form, 'book_request': book_request})


@login_required
@user_passes_test(is_student)
def request_book(request, book_id):
	book = get_object_or_404(Book, pk=book_id)
	if request.method != 'POST':
		return redirect('book_list')

	if BookRequest.objects.filter(member=request.user, book=book, status=BookRequest.STATUS_PENDING).exists():
		messages.info(request, 'You already have a pending request for this book.')
		return redirect('book_list')

	form = BookRequestForm(request.POST)
	if form.is_valid():
		book_request = form.save(commit=False)
		book_request.member = request.user
		book_request.book = book
		book_request.save()
		messages.success(request, f'Request submitted for {book.title}. Librarian will review and issue it.')
	else:
		messages.error(request, 'Request could not be submitted. Please try again.')

	return redirect('book_list')


@login_required
@user_passes_test(is_librarian)
def book_requests(request):
	status = request.GET.get('status', '').strip().lower()
	requests_qs = BookRequest.objects.select_related('member', 'book', 'reviewed_by').order_by('requested_at', 'pk')

	if status in {BookRequest.STATUS_PENDING, BookRequest.STATUS_ISSUED, BookRequest.STATUS_REJECTED}:
		requests_qs = requests_qs.filter(status=status)

	return render(
		request,
		'library/book_requests.html',
		{
			'book_requests': requests_qs,
			'selected_status': status,
		},
	)


@login_required
@user_passes_test(is_librarian)
def reject_book_request(request, request_id):
	book_request = get_object_or_404(BookRequest, pk=request_id)
	if book_request.status == BookRequest.STATUS_PENDING:
		book_request.status = BookRequest.STATUS_REJECTED
		book_request.reviewed_by = request.user
		book_request.reviewed_at = timezone.now()
		book_request.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
		messages.success(request, 'Book request rejected.')
	else:
		messages.info(request, 'This request is already processed.')
	return redirect('book_requests')


@login_required
@user_passes_test(is_librarian)
def circulation_desk(request):
	checkout_form = QuickCheckoutForm(prefix='out')
	checkin_form = QuickCheckinForm(prefix='in')

	if request.method == 'POST':
		action = request.POST.get('action')
		if action == 'checkin':
			checkout_form = QuickCheckoutForm(request.POST, prefix='out')
			if checkout_form.is_valid():
				member = checkout_form.cleaned_data['member']
				book = checkout_form.cleaned_data['book']
				with transaction.atomic():
					locked_book = Book.objects.select_for_update().get(pk=book.pk)
					active_count = BookIssue.objects.filter(book=locked_book, returned_at__isnull=True).count()
					if active_count >= locked_book.total_copies:
						checkout_form.add_error('book_isbn', 'Book is currently unavailable.')
					else:
						issue = BookIssue(
							member=member,
							book=locked_book,
							due_date=BookIssue.default_due_date(QuickCheckoutForm.ISSUE_PERIOD_DAYS),
							fine_per_day=BookIssue.FINE_PER_DAY_INR,
						)
						issue.save()
						messages.success(request, f'Checked in {locked_book.title} (issued) to {member.username}.')
						return redirect('circulation_desk')

		if action == 'checkout':
			checkin_form = QuickCheckinForm(request.POST, prefix='in')
			if checkin_form.is_valid():
				issue = checkin_form.cleaned_data['issue']
				with transaction.atomic():
					issue = BookIssue.objects.select_for_update().get(pk=issue.pk)
					if issue.returned_at:
						messages.info(request, 'This issue record is already returned.')
					else:
						issue.mark_returned()
						messages.success(request, f'Checked out {issue.book.title} (returned). Fine: Rs. {issue.fine_amount}')
				return redirect('circulation_desk')

	return render(
		request,
		'library/circulation_desk.html',
		{
			'checkout_form': checkout_form,
			'checkin_form': checkin_form,
		},
	)


@login_required
def manage_issues(request):
	query = request.GET.get('q', '').strip()
	status = request.GET.get('status', '').strip().lower()

	if is_librarian(request.user):
		issues = BookIssue.objects.select_related('book', 'member')
	elif is_student(request.user):
		issues = BookIssue.objects.filter(member=request.user).select_related('book', 'member')
	else:
		return HttpResponseForbidden('Unauthorized role.')

	if query:
		issues = issues.filter(
			Q(member__username__icontains=query)
			| Q(book__title__icontains=query)
			| Q(book__author__icontains=query)
			| Q(book__isbn__icontains=query)
		)

	returned_count = issues.filter(returned_at__isnull=False).count()
	active_count = issues.filter(returned_at__isnull=True).count()
	base_issues = issues

	overdue_books_count = 0
	overdue_days_total = 0
	pending_fines_total = Decimal('0.00')
	for issue in base_issues:
		if not issue.returned_at and issue.overdue_days > 0:
			overdue_books_count += 1
			overdue_days_total += issue.overdue_days
			pending_fines_total += issue.calculate_fine()

	if status == 'pending':
		issues = issues.filter(returned_at__isnull=True)
	elif status == 'returned':
		issues = issues.filter(returned_at__isnull=False)

	for issue in issues:
		if not issue.returned_at and issue.overdue_days > 0:
			issue.pending_fine_amount = issue.calculate_fine()
		else:
			issue.pending_fine_amount = None

	total_records_count = issues.count()

	return render(
		request,
		'library/issue_list.html',
		{
			'issues': issues,
			'is_librarian': is_librarian(request.user),
			'query': query,
			'selected_status': status,
			'returned_count': returned_count,
			'active_count': active_count,
			'total_records_count': total_records_count,
			'overdue_books_count': overdue_books_count,
			'overdue_days_total': overdue_days_total,
			'pending_fines_total': pending_fines_total,
		},
	)


@login_required
@user_passes_test(is_student)
def request_renewal(request, issue_id):
	issue = get_object_or_404(BookIssue, pk=issue_id, member=request.user, returned_at__isnull=True)
	
	if BookRenewal.objects.filter(issue=issue, status=BookRenewal.STATUS_PENDING).exists():
		messages.info(request, 'You already have a pending renewal request for this book.')
		return redirect('manage_issues')

	if request.method == 'POST':
		form = BookRenewalForm(request.POST)
		if form.is_valid():
			renewal = form.save(commit=False)
			renewal.issue = issue
			renewal.member = request.user
			renewal.save()
			messages.success(request, f'Renewal request submitted for {issue.book.title}. Librarian will review shortly.')
			return redirect('manage_issues')
	else:
		form = BookRenewalForm()
	
	return render(request, 'library/request_renewal.html', {'form': form, 'issue': issue})


@login_required
@user_passes_test(is_librarian)
def manage_renewals(request):
	status = request.GET.get('status', '').strip().lower()
	query = request.GET.get('q', '').strip()
	renewals = BookRenewal.objects.select_related('member', 'issue__book', 'reviewed_by')

	if status in {BookRenewal.STATUS_PENDING, BookRenewal.STATUS_APPROVED, BookRenewal.STATUS_REJECTED}:
		renewals = renewals.filter(status=status)
	else:
		renewals = renewals.filter(status=BookRenewal.STATUS_PENDING)

	if query:
		renewals = renewals.filter(
			Q(member__username__icontains=query)
			| Q(issue__book__title__icontains=query)
			| Q(issue__book__isbn__icontains=query)
		)

	return render(
		request,
		'library/manage_renewals.html',
		{
			'renewals': renewals,
			'selected_status': status,
			'query': query,
		},
	)


@login_required
@user_passes_test(is_librarian)
def approve_renewal(request, renewal_id):
	renewal = get_object_or_404(BookRenewal, pk=renewal_id)
	
	if renewal.status == BookRenewal.STATUS_PENDING:
		with transaction.atomic():
			renewal.status = BookRenewal.STATUS_APPROVED
			renewal.reviewed_by = request.user
			renewal.reviewed_at = timezone.now()
			new_due_date = renewal.issue.due_date + timedelta(days=14)
			renewal.new_due_date = new_due_date
			renewal.issue.due_date = new_due_date
			renewal.issue.save(update_fields=['due_date'])
			renewal.save(update_fields=['status', 'reviewed_by', 'reviewed_at', 'new_due_date'])
		messages.success(request, f'Book renewal approved. New due date: {new_due_date.strftime("%B %d, %Y")}')
	else:
		messages.info(request, 'This renewal request is already processed.')
	
	return redirect('manage_renewals')


@login_required
@user_passes_test(is_librarian)
def reject_renewal(request, renewal_id):
	renewal = get_object_or_404(BookRenewal, pk=renewal_id)
	
	if renewal.status == BookRenewal.STATUS_PENDING:
		renewal.status = BookRenewal.STATUS_REJECTED
		renewal.reviewed_by = request.user
		renewal.reviewed_at = timezone.now()
		renewal.save(update_fields=['status', 'reviewed_by', 'reviewed_at'])
		messages.success(request, 'Book renewal request rejected.')
	else:
		messages.info(request, 'This renewal request is already processed.')
	
	return redirect('manage_renewals')


@login_required
@user_passes_test(is_librarian)
def return_book(request, issue_id):
	issue = get_object_or_404(BookIssue, pk=issue_id)
	if issue.returned_at:
		messages.info(request, 'This book has already been returned.')
	else:
		with transaction.atomic():
			issue = BookIssue.objects.select_for_update().get(pk=issue.pk)
			if issue.returned_at:
				messages.info(request, 'This book has already been returned.')
			else:
				issue.mark_returned()
				issue.book.allocate_waitlisted_requests(reviewed_by=request.user)
				messages.success(request, f'Book returned. Fine: Rs. {issue.fine_amount}')
	return redirect('manage_issues')


@login_required
def student_history(request):
	issues = list(BookIssue.objects.filter(member=request.user).select_related('book'))
	returned_count = 0
	with_fine_count = 0
	pending_fine_total = Decimal('0.00')

	for issue in issues:
		if issue.returned_at:
			returned_count += 1
			issue.display_fine_amount = issue.fine_amount or Decimal('0.00')
			continue

		if issue.is_overdue:
			issue.display_fine_amount = issue.calculate_fine()
			with_fine_count += 1
			pending_fine_total += issue.display_fine_amount
		else:
			issue.display_fine_amount = Decimal('0.00')

	return render(
		request,
		'library/student_history.html',
		{
			'issues': issues,
			'returned_count': returned_count,
			'with_fine_count': with_fine_count,
			'pending_fine_total': pending_fine_total,
		},
	)


@login_required
def user_profile_data(request):
	"""API endpoint to return user profile data for QR code display"""
	user = request.user
	profile_data = {
		'username': user.username,
		'email': user.email,
	}
	
	if is_student(user):
		profile = getattr(user, 'profile', None)
		profile_data.update({
			'first_name': user.first_name,
			'last_name': user.last_name,
			'full_name': f"{user.first_name} {user.last_name}",
			'branch': profile.branch if profile else '',
			'roll_number': profile.roll_number if profile else '',
		})
	
	return JsonResponse(profile_data)


@login_required
def generate_qrcode_image(request):
	"""Generate QR code image for user profile"""
	import io
	import base64
	
	user = request.user
	
	# Prepare data for QR code
	if is_student(user):
		profile = getattr(user, 'profile', None)
		branch = profile.branch if profile else ''
		roll_number = profile.roll_number if profile else ''
		full_name = f"{user.first_name} {user.last_name}".strip() or user.username
		qr_data = (
			f"NAME: {full_name}\n"
			f"ROLL: {roll_number}\n"
			f"BRANCH: {branch}\n"
			f"EMAIL: {user.email}"
		)
	else:
		qr_data = (
			f"NAME: {user.get_full_name().strip() or user.username}\n"
			"ROLL: \n"
			"BRANCH: \n"
			f"EMAIL: {user.email}"
		)

	try:
		import qrcode  # pyright: ignore[reportMissingModuleSource]
	except ModuleNotFoundError:
		# Frontend already has JS fallback; return payload without server QR image.
		return JsonResponse({
			'qrcode': None,
			'data': qr_data,
			'fallback': True,
			'message': 'Server QR library unavailable. Use client-side QR fallback.',
		})
	
	try:
		# Generate QR code
		qr = qrcode.QRCode(
			version=None,
			error_correction=qrcode.constants.ERROR_CORRECT_H,
			box_size=12,
			border=4,
		)
		qr.add_data(qr_data)
		qr.make(fit=True)

		# Create image
		img = qr.make_image(fill_color="black", back_color="white")

		# Convert to base64
		buffer = io.BytesIO()
		img.save(buffer, format='PNG')
		buffer.seek(0)
		qr_base64 = base64.b64encode(buffer.getvalue()).decode()

		return JsonResponse({
			'qrcode': f'data:image/png;base64,{qr_base64}',
			'data': qr_data,
		})
	except Exception as exc:
		# Keep endpoint non-fatal and let browser QR fallback render.
		return JsonResponse({
			'qrcode': None,
			'data': qr_data,
			'fallback': True,
			'message': f'QR generation failed: {exc}',
		})


@login_required
@user_passes_test(is_librarian)
def live_stats(request):
	return JsonResponse(_librarian_stats())
