from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("listing/all", views.all, name="all"),
    path("listing/closed", views.closed, name='closed'),
    path("categories", views.categories, name="categories"),
    path("category/<str:category_name>", views.listing_category, name="listing_category"),
    path("watchlist", views.watchlists, name="watchlists"),
    path("watchlist/<int:id>", views.watchlist, name="watchlist"),
    path("create", views.create, name="create"),
    path("listing/<int:id>", views.listing, name="listing"),
    path("listing/<str:username>", views.listed_by, name="listed_by"),
    path("comment/<int:id>", views.comment, name="comment"),
    path("bid/<int:id>", views.bid, name="bid"),
    path("close/<int:id>", views.close, name="close"),
    path("activate/<int:id>", views.activate, name="activate"),
    path("mylistings", views.my_listings, name="my_listings"),
    path("mybids", views.my_bids, name="my_bids"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("success", views.success_page, name="success_page"),

    # Twitch authentication
    path('create_live_auctions/', views.create_live_auctions, name='create_live_auctions'),
    path("twitch/authenticate", views.twitch_authenticate, name="twitch_authenticate"),
    path("twitch/callback", views.twitch_callback, name="twitch_callback"),
    path("live_auctions", views.live_auctions, name="live_auctions"),
    path("live_stream/<int:auction_id>", views.live_stream, name="live_stream"),
    path('live_stream_auction/<int:auction_id>/', views.live_stream_auction, name='live_stream_auction'),
    path('all-live-auctions/', views.all_live_auctions, name='all_live_auctions'),
]
