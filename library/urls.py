from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.student_signup, name='student_signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('books/', views.book_list, name='book_list'),
    path('books/barcode/<str:barcode_number>/', views.book_barcode_detail, name='book_barcode_detail'),
    path('books/add/', views.book_create, name='book_create'),
    path('books/<int:pk>/edit/', views.book_update, name='book_update'),
    path('books/<int:pk>/delete/', views.book_delete, name='book_delete'),
    path('books/<int:book_id>/request/', views.request_book, name='request_book'),
    path('book-requests/', views.book_requests, name='book_requests'),
    path('book-requests/<int:request_id>/reject/', views.reject_book_request, name='reject_book_request'),
    path('issues/', views.manage_issues, name='manage_issues'),
    path('issues/new/', views.issue_book, name='issue_book'),
    path('issues/<int:issue_id>/renew/', views.request_renewal, name='request_renewal'),
    path('renewals/', views.manage_renewals, name='manage_renewals'),
    path('renewals/<int:renewal_id>/approve/', views.approve_renewal, name='approve_renewal'),
    path('renewals/<int:renewal_id>/reject/', views.reject_renewal, name='reject_renewal'),
    path('circulation/', views.circulation_desk, name='circulation_desk'),
    path('issues/<int:issue_id>/return/', views.return_book, name='return_book'),
    path('api/live-stats/', views.live_stats, name='live_stats'),
    path('api/user-profile/', views.user_profile_data, name='user_profile_api'),
    path('api/generate-qrcode/', views.generate_qrcode_image, name='generate_qrcode'),
    path('my-history/', views.student_history, name='student_history'),
]
