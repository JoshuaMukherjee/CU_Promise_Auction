from django.urls import path
from django.contrib.staticfiles.storage import staticfiles_storage
from django.views.generic.base import RedirectView

from . import views

urlpatterns = [
    path("favicon.ico", RedirectView.as_view(url=staticfiles_storage.url("favicon.ico")),),
    path('', views.NameInputView.as_view(), name='name_input'),
    path('bidding/', views.BiddingView.as_view(), name='bidding'),
    path('bidding/update_bids/', views.update_bids, name='update_bids'),
    path('bidding/add_bid/<int:item_id>/<str:price>/<str:name>/<str:phone_number>/', views.add_bid, name='add_bid'),
    path('message_generator/', views.MessageGeneratorView.as_view(), name='message_generator'),
]
